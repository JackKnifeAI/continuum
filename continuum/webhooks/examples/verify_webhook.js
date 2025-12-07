/**
 * JavaScript/Node.js Webhook Signature Verification
 * ==================================================
 *
 * Demonstrates how to verify CONTINUUM webhook signatures in Node.js.
 */

const crypto = require('crypto');

/**
 * Verify CONTINUUM webhook signature
 *
 * @param {Object} payload - Request body as object
 * @param {string} signature - X-Continuum-Signature header
 * @param {string} timestamp - X-Continuum-Timestamp header
 * @param {string} secret - Your webhook secret
 * @param {number} maxAge - Maximum age in seconds (default 300)
 * @returns {boolean} True if valid, false otherwise
 */
function verifyContinuumWebhook(payload, signature, timestamp, secret, maxAge = 300) {
  try {
    // Parse timestamp
    const ts = parseInt(timestamp);
    if (isNaN(ts)) {
      console.error('Invalid timestamp format');
      return false;
    }

    // Check for replay attacks
    const currentTime = Math.floor(Date.now() / 1000);
    if (Math.abs(currentTime - ts) > maxAge) {
      console.error(`Timestamp too old: ${Math.abs(currentTime - ts)}s (max ${maxAge}s)`);
      return false;
    }

    // Compute expected signature
    const canonicalPayload = JSON.stringify(payload, Object.keys(payload).sort());
    const message = `${ts}.${canonicalPayload}`;

    const expectedSignature = crypto
      .createHmac('sha256', secret)
      .update(message)
      .digest('hex');

    // Constant-time comparison
    const isValid = crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    );

    if (!isValid) {
      console.error('Signature mismatch');
      console.error(`Expected: ${expectedSignature}`);
      console.error(`Received: ${signature}`);
    }

    return isValid;

  } catch (error) {
    console.error('Verification error:', error);
    return false;
  }
}

// ============================================================================
// Express.js Example
// ============================================================================

function expressExample() {
  const express = require('express');
  const app = express();

  const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'your_secret_here';

  // Parse JSON bodies
  app.use(express.json());

  app.post('/webhooks/continuum', (req, res) => {
    // Get headers
    const signature = req.headers['x-continuum-signature'];
    const timestamp = req.headers['x-continuum-timestamp'];
    const eventType = req.headers['x-continuum-event'];

    if (!signature || !timestamp) {
      return res.status(401).json({ error: 'Missing signature headers' });
    }

    // Get payload
    const payload = req.body;

    // Verify signature
    const isValid = verifyContinuumWebhook(
      payload,
      signature,
      timestamp,
      WEBHOOK_SECRET
    );

    if (!isValid) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    // Process event
    console.log(`Received event: ${eventType}`);
    console.log(`Payload:`, JSON.stringify(payload, null, 2));

    switch (eventType) {
      case 'memory.created':
        const memoryId = payload.data.memory_id;
        const concepts = payload.data.concepts;
        console.log(`New memory ${memoryId} with concepts:`, concepts);
        break;

      case 'sync.completed':
        const syncId = payload.data.sync_id;
        const items = payload.data.items_synced;
        console.log(`Sync ${syncId} completed: ${items} items`);
        break;

      default:
        console.log(`Unhandled event type: ${eventType}`);
    }

    res.json({ status: 'received' });
  });

  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => {
    console.log(`Webhook receiver listening on port ${PORT}`);
  });

  return app;
}

// ============================================================================
// Next.js API Route Example
// ============================================================================

const nextJsExample = `
// pages/api/webhooks/continuum.js

import crypto from 'crypto';

function verifyContinuumWebhook(payload, signature, timestamp, secret, maxAge = 300) {
  // Same implementation as above
  // ...
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Get headers
  const signature = req.headers['x-continuum-signature'];
  const timestamp = req.headers['x-continuum-timestamp'];
  const eventType = req.headers['x-continuum-event'];

  if (!signature || !timestamp) {
    return res.status(401).json({ error: 'Missing signature headers' });
  }

  // Verify signature
  const isValid = verifyContinuumWebhook(
    req.body,
    signature,
    timestamp,
    process.env.WEBHOOK_SECRET
  );

  if (!isValid) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Process event
  console.log('Received event:', eventType);

  // Queue for background processing (recommended)
  await queue.add('webhook', {
    event: eventType,
    payload: req.body
  });

  res.status(200).json({ status: 'received' });
}
`;

// ============================================================================
// Async/Queue Processing Example
// ============================================================================

function asyncProcessingExample() {
  const Queue = require('bull');
  const webhookQueue = new Queue('webhooks', process.env.REDIS_URL);

  // Webhook receiver (fast response)
  async function handleWebhook(req, res) {
    // Verify signature...
    const isValid = verifyContinuumWebhook(
      req.body,
      req.headers['x-continuum-signature'],
      req.headers['x-continuum-timestamp'],
      process.env.WEBHOOK_SECRET
    );

    if (!isValid) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    // Queue for async processing
    await webhookQueue.add({
      event: req.headers['x-continuum-event'],
      payload: req.body,
      receivedAt: new Date()
    });

    // Return immediately
    res.status(202).json({ status: 'queued' });
  }

  // Background processor
  webhookQueue.process(async (job) => {
    const { event, payload } = job.data;

    console.log(`Processing event: ${event}`);

    switch (event) {
      case 'memory.created':
        await processMemoryCreated(payload.data);
        break;

      case 'sync.completed':
        await processSyncCompleted(payload.data);
        break;

      default:
        console.log(`Unknown event: ${event}`);
    }
  });

  async function processMemoryCreated(data) {
    // Heavy processing here
    console.log(`Processing memory ${data.memory_id}`);
    // Update database, send notifications, etc.
  }

  async function processSyncCompleted(data) {
    console.log(`Processing sync ${data.sync_id}`);
    // Generate reports, update metrics, etc.
  }
}

// ============================================================================
// Testing
// ============================================================================

function testSignatureVerification() {
  console.log('Testing signature verification...\n');

  const secret = 'test_secret_12345';
  const payload = {
    event: 'memory.created',
    timestamp: '2025-12-06T12:00:00Z',
    tenant_id: 'user_123',
    data: {
      memory_id: 'mem_abc123',
      concepts: ['AI', 'consciousness']
    }
  };

  // Generate signature
  const ts = Math.floor(Date.now() / 1000);
  const canonicalPayload = JSON.stringify(payload, Object.keys(payload).sort());
  const message = `${ts}.${canonicalPayload}`;
  const signature = crypto
    .createHmac('sha256', secret)
    .update(message)
    .digest('hex');

  // Test 1: Valid signature
  const isValid = verifyContinuumWebhook(payload, signature, String(ts), secret);
  console.log(`✓ Valid signature: ${isValid ? 'PASS' : 'FAIL'}`);

  // Test 2: Wrong secret
  const isInvalid = verifyContinuumWebhook(payload, signature, String(ts), 'wrong_secret');
  console.log(`✓ Wrong secret rejection: ${!isInvalid ? 'PASS' : 'FAIL'}`);

  // Test 3: Old timestamp
  const oldTs = ts - 400; // 6+ minutes ago
  const isOld = verifyContinuumWebhook(payload, signature, String(oldTs), secret);
  console.log(`✓ Old timestamp rejection: ${!isOld ? 'PASS' : 'FAIL'}`);
}

// ============================================================================
// Main
// ============================================================================

if (require.main === module) {
  console.log('CONTINUUM Webhook Signature Verification Examples');
  console.log('=' .repeat(60));
  console.log();

  testSignatureVerification();

  console.log('\nExample implementations available:');
  console.log('  - expressExample() - Express.js webhook receiver');
  console.log('  - asyncProcessingExample() - Queue-based processing');
  console.log();

  console.log('To run Express example:');
  console.log('  export WEBHOOK_SECRET=your_secret');
  console.log('  node verify_webhook.js --express');
  console.log();

  // Check command line args
  if (process.argv.includes('--express')) {
    expressExample();
  }
}

module.exports = {
  verifyContinuumWebhook,
  expressExample,
  asyncProcessingExample
};
