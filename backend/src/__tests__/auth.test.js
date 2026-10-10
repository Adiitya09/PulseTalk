/**
 * Authentication Tests
 * Run with: npm test
 */

const request = require('supertest');
const mongoose = require('mongoose');
const app = require('../index');

describe('Auth Endpoints', () => {
  afterAll(async () => {
    await mongoose.connection.close();
  });
  describe('POST /api/auth/register', () => {
    it('should register a new user', async () => {
      const response = await request(app)
        .post('/api/auth/register')
        .send({
          email: `test${Date.now()}@example.com`,
          password: 'Test1234',
          name: 'Test User'
        });

      expect(response.status).toBe(201);
      expect(response.body).toHaveProperty('accessToken');
      expect(response.body.user).toHaveProperty('email');
    });

    it('should reject invalid email', async () => {
      const response = await request(app)
        .post('/api/auth/register')
        .send({
          email: 'invalid-email',
          password: 'Test1234',
          name: 'Test User'
        });

      expect(response.status).toBe(400);
    });

    it('should reject weak password', async () => {
      const response = await request(app)
        .post('/api/auth/register')
        .send({
          email: 'test@example.com',
          password: 'weak',
          name: 'Test User'
        });

      expect(response.status).toBe(400);
    });
  });

  describe('POST /api/auth/login', () => {
    it('should login with valid credentials', async () => {
      // First register
      const email = `test${Date.now()}@example.com`;
      await request(app)
        .post('/api/auth/register')
        .send({
          email,
          password: 'Test1234',
          name: 'Test User'
        });

      // Then login
      const response = await request(app)
        .post('/api/auth/login')
        .send({
          email,
          password: 'Test1234'
        });

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('accessToken');
    });

    it('should reject invalid credentials', async () => {
      const response = await request(app)
        .post('/api/auth/login')
        .send({
          email: 'nonexistent@example.com',
          password: 'WrongPassword'
        });

      expect(response.status).toBe(401);
    });
  });
});
