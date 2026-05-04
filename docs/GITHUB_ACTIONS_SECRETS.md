**GitHub Actions Secrets Checklist**

This file provides a step-by-step checklist for setting up GitHub Actions secrets for your repository.

Prerequisites
- GitHub repository admin access
- Test admin credentials (do NOT use production credentials)
- Access to your testing/staging environment URL

Step-by-Step Setup

1. Navigate to GitHub Secrets:
   - Go to your repository on GitHub.com
   - Click Settings (top navigation)
   - Click "Secrets and variables" → "Actions" (left sidebar)
   - Click "New repository secret" button

2. Create secret: `E2E_BASE_URL`
   - Name: `E2E_BASE_URL`
   - Value: Full URL of your test environment, e.g.:
     - For staging: `https://staging-api.example.com`
     - For local testing: `http://127.0.0.1:5000`
   - Click "Add secret"

3. Create secret: `E2E_ADMIN_USER`
   - Name: `E2E_ADMIN_USER`
   - Value: Test admin email/username (e.g., `admin@example.com`)
   - Click "Add secret"

4. Create secret: `E2E_ADMIN_PW`
   - Name: `E2E_ADMIN_PW`
   - Value: Password for the test admin account
   - ⚠️  Use a test account, NOT your production password
   - Click "Add secret"

5. Verify secrets are added:
   - Return to Settings → Secrets and variables → Actions
   - You should see three secrets listed (values are masked):
     - E2E_ADMIN_PW
     - E2E_ADMIN_USER
     - E2E_BASE_URL

Verifying Secrets Work

After adding secrets, you can verify they're set up correctly:
1. Go to Actions tab
2. Click the "E2E" workflow
3. Click "Run workflow" (top right)
4. Select the branch (main)
5. Click "Run workflow" (green button)
6. The workflow will start; click on the running job to view logs
7. If secrets are set correctly, you'll see the test connect to your environment

Troubleshooting

- Secrets not working? Try:
  1. Refresh the page
  2. Verify secret names match exactly (case-sensitive)
  3. Ensure values don't have extra spaces before/after
  4. Check that test admin account exists and is accessible

- Workflow fails with "403 Forbidden"?
  1. Verify the `E2E_BASE_URL` is correct
  2. Confirm admin credentials are valid
  3. Check that the test environment allows GitHub Actions IP ranges (if applicable)

- Workflow can't find Playwright?
  1. The E2E workflow installs Playwright automatically
  2. This may take 1-2 minutes on the first run
  3. Subsequent runs will be faster (cached dependencies)

Re-running E2E Tests

Once secrets are configured, you can manually run E2E tests anytime:
1. Go to Actions tab
2. Click "E2E" workflow (left sidebar)
3. Click "Run workflow" (top right)
4. Select branch and click "Run workflow"

Security Best Practices

- ✅ Keep secrets in GitHub (never commit to code)
- ✅ Use test account credentials, never production
- ✅ Rotate secrets periodically (every 90 days recommended)
- ✅ Use environment-specific secrets for staging vs. production
- ✅ Audit who has access to secrets (limit to team members)
- ⚠️  Don't share secrets in chat, emails, or commit messages
- ⚠️  Don't log secrets in workflow output (GitHub masks them automatically)

Advanced: Using Production Secrets (for automated deployments)

If you want to run E2E against production automatically:
1. Create separate secrets: `PROD_E2E_BASE_URL`, `PROD_E2E_ADMIN_USER`, `PROD_E2E_ADMIN_PW`
2. Use a read-only test account on production (created just for CI/CD)
3. Rotate credentials frequently
4. Consider using a dedicated CI/CD service account with minimal permissions

Complete! Your CI/CD pipeline is now ready to run E2E tests.
