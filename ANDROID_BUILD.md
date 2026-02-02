# Building Family Hub Android APK

This guide explains how to build the Android APK for Family Hub.

## Prerequisites

- Node.js 18+ and Yarn
- Java JDK 17
- Android Studio or Android SDK Command-line Tools
- (Optional) Android device or emulator for testing

## Quick Build (GitHub Actions)

The easiest way to get an APK is through GitHub Actions:

1. Push your code to GitHub
2. Go to Actions → "Build Android APK"
3. Click "Run workflow"
4. Download the APK from the workflow artifacts

## Local Build

### 1. Install Dependencies

```bash
# Install frontend dependencies
cd frontend
yarn install

# Build the web app
yarn build
```

### 2. Set Up Android SDK

**Option A: Android Studio (Recommended)**
1. Download [Android Studio](https://developer.android.com/studio)
2. Open Android Studio → SDK Manager
3. Install Android SDK 34 and Build Tools

**Option B: Command Line Only**
```bash
# Install sdkmanager (varies by OS)
# macOS with Homebrew:
brew install --cask android-commandlinetools

# Accept licenses
sdkmanager --licenses

# Install required SDK components
sdkmanager "platforms;android-34" "build-tools;34.0.0"
```

### 3. Sync Capacitor

```bash
cd frontend
npx cap sync android
```

### 4. Build Debug APK

```bash
cd frontend/android
./gradlew assembleDebug
```

APK location: `frontend/android/app/build/outputs/apk/debug/app-debug.apk`

### 5. Build Release APK (Unsigned)

```bash
cd frontend/android
./gradlew assembleRelease
```

APK location: `frontend/android/app/build/outputs/apk/release/app-release-unsigned.apk`

## Signing the APK

### Generate a Keystore

```bash
keytool -genkey -v -keystore family-hub.keystore \
  -alias family-hub -keyalg RSA -keysize 2048 -validity 10000
```

### Sign the APK

**Option A: Using Environment Variables**
```bash
export ANDROID_KEYSTORE_PATH=/path/to/family-hub.keystore
export ANDROID_KEYSTORE_PASSWORD=your-store-password
export ANDROID_KEY_ALIAS=family-hub
export ANDROID_KEY_PASSWORD=your-key-password

cd frontend/android
./gradlew assembleRelease
```

**Option B: Using apksigner**
```bash
# Build unsigned APK first
./gradlew assembleRelease

# Sign it
apksigner sign --ks family-hub.keystore \
  --out app-release-signed.apk \
  app/build/outputs/apk/release/app-release-unsigned.apk
```

## GitHub Actions Setup for Signed APKs

1. Generate your keystore (see above)
2. Encode keystore as base64:
   ```bash
   base64 -i family-hub.keystore | tr -d '\n' > keystore.txt
   ```
3. Add these secrets to your GitHub repository:
   - `ANDROID_SIGNING_KEY`: Contents of keystore.txt
   - `ANDROID_KEY_ALIAS`: Your key alias
   - `ANDROID_KEYSTORE_PASSWORD`: Keystore password
   - `ANDROID_KEY_PASSWORD`: Key password

4. Push a tag to trigger signed release:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

## Configuring Server URL

### For Self-Hosted Servers

Users can configure their server URL in the app:
1. Open the app
2. Tap "Self-Hosted Server" on login screen
3. Enter server URL (e.g., `https://family.yourdomain.com`)
4. Test connection and save

### Hardcoding a Default Server (Optional)

Edit `frontend/capacitor.config.json`:
```json
{
  "appId": "com.familyhub.app",
  "appName": "Family Hub",
  "webDir": "build",
  "server": {
    "url": "https://your-default-server.com",
    "cleartext": false
  }
}
```

## Testing

### On Emulator
```bash
cd frontend/android
./gradlew installDebug
# App will install on connected emulator
```

### On Device
1. Enable "Developer Options" on your Android device
2. Enable "USB Debugging"
3. Connect via USB
4. Run:
   ```bash
   cd frontend/android
   ./gradlew installDebug
   ```

### ADB Install
```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

## Troubleshooting

### Build Fails with "SDK not found"
```bash
# Create local.properties
echo "sdk.dir=$ANDROID_HOME" > frontend/android/local.properties
```

### Gradle Wrapper Issues
```bash
cd frontend/android
gradle wrapper --gradle-version 8.4
```

### Camera Not Working
Make sure permissions are granted in Android Settings → Apps → Family Hub → Permissions

## App Store Publishing

### Google Play Store

1. Create signed release APK (or App Bundle)
2. Create [Google Play Console](https://play.google.com/console) account
3. Create new app
4. Upload APK/AAB
5. Complete store listing
6. Submit for review

### Building App Bundle (AAB) for Play Store
```bash
cd frontend/android
./gradlew bundleRelease
```

Bundle location: `frontend/android/app/build/outputs/bundle/release/app-release.aab`

## File Structure

```
frontend/
├── android/
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── AndroidManifest.xml
│   │   │   ├── java/.../MainActivity.java
│   │   │   └── res/
│   │   │       ├── drawable/          # Icons & splash
│   │   │       ├── values/            # Colors, strings
│   │   │       └── mipmap-*/          # App icons
│   │   └── build.gradle
│   └── build.gradle
├── capacitor.config.json
└── build/                             # Web build output
```
