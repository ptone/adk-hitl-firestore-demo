// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDF5VKgo_SREIRLbmGO328-5XmC9zkRbhs",
  authDomain: "ptone-misc.firebaseapp.com",
  databaseURL: "https://ptone-misc.firebaseio.com",
  projectId: "ptone-misc",
  storageBucket: "ptone-misc.appspot.com",
  messagingSenderId: "109110420228",
  appId: "1:109110420228:web:2bcc07a269b93d5956e651"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

export { db };