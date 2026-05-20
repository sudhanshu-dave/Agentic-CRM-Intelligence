# API Documentation Policy

## API Versions

API v1 is deprecated and scheduled for sunset on December 31, 2023. Customers should migrate to API v2 before the sunset date.

## API v2 Requirements

API v2 requires updated authentication headers, workspace identification, pagination support, and webhook signature validation. Requests to v2 endpoints may require the X-Workspace-ID header in addition to the API key.

## Rate Limits

Standard tier customers receive baseline API rate limits. Professional tier customers receive higher limits. Enterprise customers may negotiate custom limits such as 5,000 or 10,000 requests per minute depending on contract terms.

## Rate Limit Increase Requests

If a customer asks for higher rate limits, the agent should check account tier and usage history before suggesting options. Enterprise rate limit requests should be routed to Sales or Customer Success for review.

## Integration Issues

For API errors such as 403, 500, webhook failures, missing headers, authentication failures, or migration blockers, the agent should classify the message as a technical issue or bug report depending on severity. Launch deadlines and production blockers should increase urgency.