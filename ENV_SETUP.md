# Using .env for Secret Management

This project uses a `.env` file to manage API credentials securely.

## Quick Setup

### 1. Copy the example file

```bash
cp .env.example .env
```

### 2. Edit `.env` with your credentials

```bash
# Open in your editor
nano .env
# or
code .env
```

Add your Trading212 API credentials:

```env
TRADING212_API_KEY=your_actual_api_key_here
TRADING212_API_SECRET=your_actual_api_secret_here
TRADING212_ENVIRONMENT=live
```

### 3. Rebuild the Docker image

```bash
cd ~/trading212
docker build -t trading212-mcp-server:latest .
```

### 4. Restart Claude Desktop

Quit and reopen Claude Desktop completely.

---

## Security Notes

✅ **Good practices:**
- `.env` is in `.gitignore` - won't be committed to git
- File permissions should be `600` (only you can read/write)
- Never share your `.env` file

⚠️ **Important:**
- The `.env` file is copied into the Docker image during build
- Rebuild the image whenever you change credentials
- Don't push images with credentials to public registries

---

## Updating Credentials

When you need to rotate your API keys:

```bash
# 1. Update .env file with new credentials
nano .env

# 2. Rebuild the image
docker build -t trading212-mcp-server:latest .

# 3. Restart Claude Desktop
```

---

## Verification

Test your credentials before rebuilding:

```bash
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Authorization: Basic $(echo -n 'YOUR_KEY:YOUR_SECRET' | base64)" \
  "https://live.trading212.com/api/v0/equity/account/info"
```

Expected: `HTTP Status: 200` with account info.

---

## File Structure

```
~/trading212/
├── .env              # Your actual credentials (NOT in git)
├── .env.example      # Template (safe to commit)
├── .gitignore        # Protects .env from git
├── Dockerfile        # Copies .env into image
└── trading212_server.py  # Loads .env at startup
```

---

## Troubleshooting

### Problem: Credentials not loading

**Check the .env file exists:**
```bash
ls -la ~/trading212/.env
```

**Verify contents:**
```bash
cat ~/trading212/.env
```

**Check file permissions:**
```bash
chmod 600 ~/trading212/.env
```

### Problem: Still seeing old credentials

**Solution:** Rebuild the image
```bash
cd ~/trading212
docker build --no-cache -t trading212-mcp-server:latest .
```

---

## Why .env?

**Advantages:**
✅ No Docker build warnings about secrets in ENV
✅ Easy to update credentials (just edit file)
✅ Protected by `.gitignore`
✅ Simple and straightforward
✅ Industry standard approach

**Trade-offs:**
⚠️ Credentials are in the image (not visible in layers though)
⚠️ Need to rebuild when changing credentials

For more secure alternatives (Docker Secrets, external secret managers), see [SECRET_MANAGEMENT.md](SECRET_MANAGEMENT.md).
