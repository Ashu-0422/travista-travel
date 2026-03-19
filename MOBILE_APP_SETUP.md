# Travista Mobile App Setup (Android + iOS)

## 1) What is already done in this repo
- PWA support added:
  - `static/manifest.webmanifest`
  - `static/sw.js`
  - `static/mobile-app.js`
  - mobile app icon (`static/icons/app-icon.svg`)
- All major templates include manifest + service worker registration.

This means your app can be installed from browser:
- Android (Chrome): `Add to Home Screen`
- iPhone (Safari): `Share -> Add to Home Screen`

## 2) For Play Store / App Store submission
Use Capacitor wrapper around your deployed web app.

### Prerequisites
- Node.js 20+
- Android Studio
- Xcode (Mac only for iOS)
- Public HTTPS URL of your Flask app

### Steps
1. Create a wrapper app:
```bash
npm create vite@latest travista-mobile -- --template vanilla
cd travista-mobile
npm install
npm install @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios
npx cap init Travista com.travista.app --web-dir=dist
```

2. In `capacitor.config.ts`, point to your live website:
```ts
const config: CapacitorConfig = {
  appId: "com.travista.app",
  appName: "Travista",
  webDir: "dist",
  server: {
    url: "https://your-domain.com",
    cleartext: false
  }
};
```

3. Build and sync:
```bash
npm run build
npx cap add android
npx cap add ios
npx cap sync
```

4. Open native projects:
```bash
npx cap open android
npx cap open ios
```

5. From Android Studio/Xcode:
- Set app icon + splash screen
- Create signed builds
- Upload to Play Store / App Store Connect

## 3) Recommended next improvements
- Add push notifications (FCM/APNs)
- Add in-app camera/file upload enhancements
- Add offline API fallback for key screens
