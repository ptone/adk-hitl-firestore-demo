const admin = require('firebase-admin');

// Initialize Firebase Admin SDK with Application Default Credentials
admin.initializeApp();

const db = admin.firestore();

const sampleApprovals = [
  // Existing items
  {
    itemName: 'Laptop Stand',
    status: 'pending',
    requestedBy: 'user1@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 100,
  },
  {
    itemName: 'Ergonomic Keyboard',
    status: 'approved',
    requestedBy: 'user2@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    approvedBy: 'admin@example.com',
    approvedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 75,
  },
  {
    itemName: 'Noise Cancelling Headphones',
    status: 'rejected',
    requestedBy: 'user3@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    rejectedBy: 'admin@example.com',
    rejectedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 250,
  },
  // Additional pending items
  {
    itemName: 'Wireless Mouse',
    status: 'pending',
    requestedBy: 'user4@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 25,
  },
  {
    itemName: 'Monitor Arm',
    status: 'pending',
    requestedBy: 'user5@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 120,
  },
  {
    itemName: 'Webcam with Ring Light',
    status: 'pending',
    requestedBy: 'user1@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 60,
  },
  {
    itemName: 'Standing Desk Converter',
    status: 'pending',
    requestedBy: 'user6@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 180,
  },
  {
    itemName: 'Docking Station',
    status: 'pending',
    requestedBy: 'user2@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 150,
  },
  // Additional approved items
  {
    itemName: 'Mechanical Keyboard',
    status: 'approved',
    requestedBy: 'user7@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    approvedBy: 'admin@example.com',
    approvedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 90,
  },
  {
    itemName: '4K Monitor',
    status: 'approved',
    requestedBy: 'user8@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    approvedBy: 'admin@example.com',
    approvedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 350,
  },
  // Additional rejected items
  {
    itemName: 'Gaming Chair',
    status: 'rejected',
    requestedBy: 'user9@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    rejectedBy: 'admin@example.com',
    rejectedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 220,
  },
  {
    itemName: 'Mini Fridge for Desk',
    status: 'rejected',
    requestedBy: 'user10@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    rejectedBy: 'admin@example.com',
    rejectedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 80,
  },
  // More pending items
  {
    itemName: 'Foot Rest',
    status: 'pending',
    requestedBy: 'user3@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 30,
  },
  {
    itemName: 'Cable Management Box',
    status: 'pending',
    requestedBy: 'user11@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 20,
  },
  {
    itemName: 'Desk Pad Large',
    status: 'pending',
    requestedBy: 'user12@example.com',
    requestedAt: admin.firestore.FieldValue.serverTimestamp(),
    amount: 40,
  }
];

async function populateApprovals() {
  const approvalsCollection = db.collection('approvals');
  console.log('Populating approvals collection with an expanded dataset...');
  for (const approval of sampleApprovals) {
    try {
      const docRef = await approvalsCollection.add(approval);
      console.log(`Added document with ID: ${docRef.id}, Item: ${approval.itemName}`);
    } catch (error) {
      console.error('Error adding document: ', error);
    }
  }
  console.log('Finished populating approvals collection.');
}

populateApprovals().then(() => {
  console.log('Successfully populated database. Closing connection.');
  return admin.app().delete(); // Ensure app termination
}).catch(error => {
  console.error('Error populating database: ', error);
  return admin.app().delete(); // Ensure app termination on error too
});