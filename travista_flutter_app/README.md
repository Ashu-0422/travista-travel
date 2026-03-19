# Travista Flutter Mobile Wrapper

This folder is a separate Flutter app wrapper for your existing Flask website.
Your current website code is unchanged.

## 1) Install Flutter (once)
- Download Flutter SDK: https://docs.flutter.dev/get-started/install/windows/mobile
- Add Flutter to PATH
- Run:
  - `flutter doctor`

## 2) Initialize Flutter project files in this folder
From repo root:
- `cd travista_flutter_app`
- `flutter create .`

Then restore these files (already prepared):
- `pubspec.yaml`
- `lib/main.dart`
- `android/app/src/main/AndroidManifest.xml`

Run:
- `flutter pub get`

## 3) Run on phone (debug)
1. Start your Flask server on laptop:
   - `python mainn.py`
2. Find laptop local IP (example `192.168.1.10`).
3. Run Flutter app with local URL:
   - `flutter run --dart-define=APP_URL=http://192.168.1.10:5000`

Phone and laptop must be on same Wi-Fi.

## 4) Production build (recommended)
Deploy your Flask app on HTTPS domain first, then build:
- `flutter build apk --release --dart-define=APP_URL=https://your-domain.com`
- `flutter build appbundle --release --dart-define=APP_URL=https://your-domain.com`

Use `.aab` for Play Store upload.

## 5) Important notes
- `android:usesCleartextTraffic="true"` allows local `http://` testing.
- For production, prefer HTTPS URL.
- If camera/file upload or notifications are needed later, we can add native permissions/plugins.
