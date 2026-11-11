# Apna eMitra Firebase integration

## Code status
- `index.html` now includes Firebase Email/Password login, a UID-restricted Admin content manager, Firestore create/edit/delete, Storage PDF/image upload, and public Firestore listeners.
- The existing homepage style and GitHub Actions job-discovery workflow are retained.
- The Firebase Web config supplied for project `apna-emitra-db9cb` has been inserted in `index.html`.

## 1. Add the Firebase Web config
In GitHub, open `index.html` and find `const firebaseConfig = {`.
Replace the six placeholder values with the object shown in Firebase Console > Project settings > General > Your apps > SDK setup and configuration > Config.

Do not add a Service Account JSON, private key, Admin SDK credentials, or any account password to this repository. Firebase Web config is designed for client-side apps; protect the project with Firebase Rules and API-key referrer restrictions.

## 2. Confirm the Admin UID
The `ADMIN_UID` constant in `index.html` is prefilled with the UID supplied in the setup conversation. Confirm it exactly matches Firebase Console > Authentication > Users. The same UID must be used in Firestore and Storage Rules.

## 3. Authentication
- Authentication > Sign-in method: enable Email/Password.
- Authentication > Users: create the one Admin account.
- Authentication > Settings > Authorized domains: add `apnaemitra.in` and `www.apnaemitra.in`. Add your GitHub Pages hostname if you test directly on that hostname.
- There is no public sign-up form in the website.

## 4. Firestore Security Rules
Go to Firestore Database > Rules and publish the following rules. These cover every collection used by the Admin dashboard and deny all other collections.

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    function isAdmin() {
      return request.auth != null
        && request.auth.uid == "ss9iFpyObDMsZLlfffJNs8TB4wRCx2";
    }

    function canReadPublished() {
      return isAdmin() || resource.data.status == "published";
    }

    match /jobs/{id} {
      allow read: if canReadPublished();
      allow create, update, delete: if isAdmin();
    }
    match /privateJobs/{id} {
      allow read: if canReadPublished();
      allow create, update, delete: if isAdmin();
    }
    match /admitCards/{id} {
      allow read: if canReadPublished();
      allow create, update, delete: if isAdmin();
    }
    match /results/{id} {
      allow read: if canReadPublished();
      allow create, update, delete: if isAdmin();
    }
    match /schemes/{id} {
      allow read: if canReadPublished();
      allow create, update, delete: if isAdmin();
    }
    match /services/{id} {
      allow read: if canReadPublished();
      allow create, update, delete: if isAdmin();
    }
    match /documents/{id} {
      allow read: if canReadPublished();
      allow create, update, delete: if isAdmin();
    }
    match /books/{id} {
      allow read: if canReadPublished();
      allow create, update, delete: if isAdmin();
    }

    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

Important: the public website queries each collection with `status == "published"`; Firestore Rules do not filter records from a broad query. The Admin list reads all documents only after a UID-matched login.

## 5. Storage Rules
Go to Storage > Rules. Use the same Admin UID. This allows visitors to read only files intentionally uploaded under `public/`; Admin-only files belong under `private/`.

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    function isAdmin() {
      return request.auth != null
        && request.auth.uid == "ss9iFpyObDMsZLlfffJNs8TB4wRCx2";
    }
    function validUpload() {
      return request.resource.size < 10 * 1024 * 1024
        && (
          request.resource.contentType == 'application/pdf'
          || request.resource.contentType == 'image/png'
          || request.resource.contentType == 'image/jpeg'
          || request.resource.contentType == 'image/webp'
        );
    }
    match /public/{allPaths=**} {
      allow read: if true;
      allow write: if isAdmin() && (request.resource == null || validUpload());
    }
    match /private/{allPaths=**} {
      allow read, write: if isAdmin();
    }
    match /{allPaths=**} {
      allow read, write: if false;
    }
  }
}
```

Do not upload personal customer files (Aadhaar, PAN, bank details, certificates with personal identifiers) into the public folder.

## 6. Using the dashboard
1. Open `https://apnaemitra.in`.
2. Click the Admin link in the navigation or scroll to Admin Access.
3. Sign in using the Firebase Admin email and password.
4. Select Government Job, Private Job, Admit Card, Result, Scheme, Service, Document Guide, or Books.
5. Fill the content, provide an official HTTPS URL where appropriate, optionally upload a PDF/image (up to 10 MB), and choose Draft or Published.
6. Published content appears in the relevant public section through Firestore listeners. Drafts remain hidden from visitors.
7. Edit and Delete actions are in the Admin content list.

## Important limitations in this first integration
- The existing assistance request form is still demo-only; it does not yet store customer requests. This needs a separate privacy-conscious Firestore rule and form change.
- The content panel is a first version. It stores general fields plus job category, qualification, location, vacancies, last date, age limit, salary, fee, official URL and optional attachment.
- This uses the Firebase browser SDK and UID-bound security rules. It is not a substitute for a trusted server for sensitive operations.
- Test public access, unauthorized users, Admin login, draft visibility, publishing, edit/delete, and upload before public launch.
