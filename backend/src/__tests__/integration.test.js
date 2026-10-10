/**
 * PulseTalk End-to-End Integration Tests
 * Tests complete flow: Auth -> ML Engine -> MongoDB -> Credit Deductions -> History & Stats
 */

const request = require('supertest');
const mongoose = require('mongoose');
const app = require('../index');
const { User, Analysis } = require('../models');

describe('End-to-End Application Integration', () => {
  let user1Token;
  let user1Id;
  let user1Email;
  let user2Token;
  let createdAnalysisId;

  beforeAll(async () => {
    user1Email = `integration_${Date.now()}@example.com`;
  });

  afterAll(async () => {
    // Clean up test users and analyses
    if (user1Email) {
      const u1 = await User.findOne({ email: user1Email });
      if (u1) {
        await Analysis.deleteMany({ user: u1._id });
        await User.deleteOne({ _id: u1._id });
      }
    }
    await mongoose.connection.close();
  });

  test('Step 1: Register new user with 100 initial analysis credits', async () => {
    const res = await request(app)
      .post('/api/auth/register')
      .send({
        email: user1Email,
        password: 'Password123!',
        name: 'Integration Tester'
      });

    user1Token = res.body.accessToken;
    user1Id = res.body.user._id || res.body.user.id;

    expect(res.status).toBe(201);
    expect(res.body).toHaveProperty('accessToken');
    expect(res.body.user).toHaveProperty('analysisCredits', 100);
    expect(res.body.user).toHaveProperty('totalAnalyses', 0);
  });

  test('Step 2: Login with registered user credentials', async () => {
    const res = await request(app)
      .post('/api/auth/login')
      .send({
        email: user1Email,
        password: 'Password123!'
      });

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('accessToken');
    expect(res.body.user.email).toBe(user1Email);
    user1Token = res.body.accessToken;
  });

  test('Step 3: Submit text analysis, communicate with ML Engine, deduct 1 credit, save in MongoDB', async () => {
    const res = await request(app)
      .post('/api/analysis')
      .set('Authorization', `Bearer ${user1Token}`)
      .send({
        text: 'PulseTalk is absolutely brilliant! I love using this platform so much!',
        title: 'Positive Feedback Test'
      });

    createdAnalysisId = res.body.analysis?._id || res.body.analysis?.id;

    expect(res.status).toBe(201);
    expect(res.body).toHaveProperty('message', 'Analysis complete');
    expect(res.body).toHaveProperty('remainingCredits', 99);
    expect(res.body.analysis).toHaveProperty('_id');
    expect(res.body.analysis.result).toHaveProperty('sentiment', 'positive');
    expect(res.body.analysis.result.sentimentScore).toBeGreaterThan(0.7);
    expect(res.body.analysis.result).toHaveProperty('confidence');
    expect(res.body.analysis.result).toHaveProperty('emotions');

    // Verify database state directly
    const userInDb = await User.findById(user1Id);
    expect(userInDb.analysisCredits).toBe(99);
    expect(userInDb.totalAnalyses).toBe(1);

    const savedAnalysis = await Analysis.findById(createdAnalysisId);
    expect(savedAnalysis).not.toBeNull();
    expect(savedAnalysis.result.sentiment).toBe('positive');
  }, 30000);

  test('Step 4: Submit neutral text analysis and verify neutral classification & second deduction', async () => {
    const res = await request(app)
      .post('/api/analysis')
      .set('Authorization', `Bearer ${user1Token}`)
      .send({
        text: 'The package arrived on Tuesday afternoon.',
        title: 'Neutral Delivery Test'
      });

    expect(res.status).toBe(201);
    expect(res.body).toHaveProperty('remainingCredits', 98);
    expect(res.body.analysis.result).toHaveProperty('sentiment', 'neutral');

    const userInDb = await User.findById(user1Id);
    expect(userInDb.analysisCredits).toBe(98);
    expect(userInDb.totalAnalyses).toBe(2);
  }, 30000);

  test('Step 5: Retrieve user analysis history and pagination', async () => {
    const res = await request(app)
      .get('/api/analysis')
      .set('Authorization', `Bearer ${user1Token}`)
      .query({ page: 1, limit: 10 });

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('analyses');
    expect(res.body.analyses.length).toBe(2);
    expect(res.body.pagination).toHaveProperty('total', 2);
  });

  test('Step 6: Retrieve single analysis by ID', async () => {
    expect(createdAnalysisId).toBeDefined();

    const res = await request(app)
      .get(`/api/analysis/${createdAnalysisId}`)
      .set('Authorization', `Bearer ${user1Token}`);

    expect(res.status).toBe(200);
    expect(res.body.analysis).toHaveProperty('_id', createdAnalysisId.toString());
    expect(res.body.analysis.title).toBe('Positive Feedback Test');
  });

  test('Step 7: Retrieve user analytics stats', async () => {
    const res = await request(app)
      .get('/api/analysis/stats')
      .set('Authorization', `Bearer ${user1Token}`);

    expect(res.status).toBe(200);
    expect(res.body.stats).toHaveProperty('total', 2);
    expect(res.body.stats).toHaveProperty('positive', 1);
    expect(res.body.stats).toHaveProperty('neutral', 1);
  });

  test('Step 8: User data isolation - another user cannot view user 1 analysis', async () => {
    const user2Email = `user2_${Date.now()}@example.com`;
    const reg2 = await request(app)
      .post('/api/auth/register')
      .send({
        email: user2Email,
        password: 'Password123!',
        name: 'User Two'
      });
    user2Token = reg2.body.accessToken;

    const res = await request(app)
      .get(`/api/analysis/${createdAnalysisId}`)
      .set('Authorization', `Bearer ${user2Token}`);

    expect(res.status).toBe(404);

    // Clean up user 2
    await User.deleteOne({ email: user2Email });
  });

  test('Step 9: Input validation - reject empty text submission', async () => {
    const res = await request(app)
      .post('/api/analysis')
      .set('Authorization', `Bearer ${user1Token}`)
      .send({
        text: '   '
      });

    expect(res.status).toBe(400);
    expect(res.body).toHaveProperty('error', 'Validation Error');
  });

  test('Step 10: Enforce credit limits - reject analysis when credits reach 0', async () => {
    // Set user credits to 0
    await User.findByIdAndUpdate(user1Id, { analysisCredits: 0 });

    const res = await request(app)
      .post('/api/analysis')
      .set('Authorization', `Bearer ${user1Token}`)
      .send({
        text: 'This should fail due to zero credits.'
      });

    expect(res.status).toBe(402);
    expect(res.body).toHaveProperty('error', 'Payment Required');
    expect(res.body).toHaveProperty('message', 'Insufficient analysis credits');
  });
});
