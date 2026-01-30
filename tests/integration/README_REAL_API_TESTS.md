# Real API Testing Guide

This guide explains how to test the video consultation feature using the **real Whereby API** instead of mocks.

## Prerequisites

1. **Whereby API Key**: You need a valid `WHEREBY_API_KEY` in your `.env` file or environment variables
   ```bash
   WHEREBY_API_KEY=your_api_key_here
   ```

2. **API Key Setup**: 
   - Get your API key from [Whereby Developer Portal](https://whereby.dev/)
   - Add it to your `.env` file: `WHEREBY_API_KEY=your_key_here`
   - Or export it: `export WHEREBY_API_KEY=your_key_here`

## Running Real API Tests

### Option 1: Run Dedicated Real API Test File

The easiest way is to run the dedicated test file that's designed for real API testing:

```bash
pytest tests/integration/test_video_consultation_real.py -v -s
```

This file:
- Automatically skips if no API key is found
- Uses the `@pytest.mark.real_api` marker to disable mocking
- Tests the complete video consultation flow with real Whereby API calls

### Option 2: Use Environment Variable (All Tests)

To disable mocking for **all tests** in a session:

```bash
REAL_API_TESTS=true pytest tests/integration/ -v -s
```

This will:
- Disable the `mock_whereby_api` fixture for all tests
- Make real API calls to Whereby
- Use your actual API key

### Option 3: Use Pytest Marker (Specific Tests)

You can mark any test to use the real API:

```python
@pytest.mark.real_api
def test_my_video_feature(client, patient_user, doctor_user):
    # This test will use real Whereby API
    ...
```

Then run:
```bash
pytest tests/integration/ -v -s -m real_api
```

## Available Real API Test Files

1. **`test_video_consultation_real.py`** - Comprehensive video consultation tests
   - Tests appointment creation with real video rooms
   - Tests patient and doctor access to video rooms
   - Tests complete booking flow
   - Tests URL accessibility

2. **`test_whereby_real.py`** - Basic Whereby API integration tests
   - Direct API calls
   - Room creation verification
   - URL validation

3. **`test_whereby_manual.py`** - Manual testing helpers
   - Quick API verification
   - Room creation for manual testing

## What Gets Tested

When running real API tests, the following are verified:

✅ **API Key Configuration**
- Verifies API key is set and valid

✅ **Video Room Generation**
- Tests `appointment.generate_video_room()` makes real API calls
- Verifies both `video_room_url` and `video_host_url` are generated
- Checks room IDs are extracted correctly

✅ **Patient Access**
- Tests patients can access video consultation pages
- Verifies patient gets the guest room URL

✅ **Doctor Access**
- Tests doctors can access video consultation pages
- Verifies doctor gets the host room URL

✅ **Complete Booking Flow**
- Tests end-to-end appointment booking with video room generation
- Verifies video rooms are created automatically for online appointments

✅ **URL Accessibility**
- Tests that generated URLs are actually accessible via HTTP
- Verifies Whereby returns valid room pages

## Example Output

When running real API tests, you'll see output like:

```
✅ API Key configured: wb_live_abc...
📋 Appointment: APT-20260123-ABCD
🎥 Video Room URL: https://sub.whereby.com/test-room-123
🎥 Host URL: https://sub.whereby.com/test-room-123?host
🎥 Room ID: test-room-123
✅ Patient can access video room
✅ Doctor can access video room
🎉 Complete video consultation flow tested successfully!
```

## Important Notes

⚠️ **API Rate Limits**: Whereby has rate limits on API calls. Running many real API tests may hit these limits.

⚠️ **Cost**: Some Whereby plans charge per room created. Check your plan before running extensive real API tests.

⚠️ **Network Required**: Real API tests require internet connectivity.

⚠️ **Test Data**: Real API tests create actual Whereby rooms that expire after the specified `endDate`. These rooms are real and can be accessed via the generated URLs.

## Troubleshooting

### "WHEREBY_API_KEY not configured"
- Make sure your `.env` file has `WHEREBY_API_KEY=your_key`
- Or export it: `export WHEREBY_API_KEY=your_key`
- Check that the key is valid in the Whereby dashboard

### "API call failed: 401"
- Your API key is invalid or expired
- Check your Whereby account and regenerate the key

### "API call failed: 429"
- You've hit rate limits
- Wait a few minutes and try again
- Consider using mocks for most tests and real API only for final verification

### Tests are still using mocks
- Make sure you're using one of the methods above
- Check that `REAL_API_TESTS=true` is set (if using that method)
- Verify the test file has `@pytest.mark.real_api` marker (if using that method)

## Best Practices

1. **Use Mocks for Most Tests**: Keep most tests using mocks for speed and reliability
2. **Real API for Integration**: Use real API tests for final integration verification
3. **CI/CD**: Consider running real API tests only in staging/production environments
4. **Rate Limiting**: Be mindful of API rate limits when running many tests
5. **Manual Verification**: Use the generated URLs to manually test video rooms in browsers

## Running Both Mocked and Real Tests

You can run both types of tests in the same session:

```bash
# Run mocked tests (default)
pytest tests/integration/test_booking_flow.py -v

# Run real API tests
REAL_API_TESTS=true pytest tests/integration/test_video_consultation_real.py -v -s
```

This way you get:
- Fast, reliable mocked tests for development
- Real API verification for integration testing




