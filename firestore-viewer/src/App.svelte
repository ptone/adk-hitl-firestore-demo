<script>
  import { onMount, onDestroy } from 'svelte';
  import { db } from './firebase.js';
  import { collection, onSnapshot, query, orderBy, where, doc, updateDoc, serverTimestamp } from 'firebase/firestore';

  let items = [];
  let isLoading = true;
  let error = null;
  let showOnlyPending = true; 
  const collectionName = 'approvals';

  let currentUnsubscribeFn = null;
  let executionCount = 0; // Debug counter

  function setupSubscription(isPendingOnly) {
    executionCount++;
    console.log(`[${executionCount}] setupSubscription called. isPendingOnly: ${isPendingOnly}, current isLoading: ${isLoading}`);

    if (currentUnsubscribeFn) {
      console.log(`[${executionCount}] Cleaning up previous Firestore listener.`);
      currentUnsubscribeFn();
      currentUnsubscribeFn = null; // Explicitly nullify
    }

    isLoading = true; // Set loading true at the start of setup
    console.log(`[${executionCount}] isLoading set to true.`);

    let q;
    if (isPendingOnly) {
      q = query(
        collection(db, collectionName),
        where("status", "==", "pending"),
        orderBy('requestedAt', 'desc')
      );
      console.log(`[${executionCount}] Setting up Firestore listener: PENDING ONLY`);
    } else {
      q = query(
        collection(db, collectionName),
        orderBy('status'), 
        orderBy('requestedAt', 'desc')
      );
      console.log(`[${executionCount}] Setting up Firestore listener: ALL ITEMS`);
    }

    currentUnsubscribeFn = onSnapshot(q, (querySnapshot) => {
      console.log(`[${executionCount}] Firestore listener update. Size: ${querySnapshot.size}. isLoading before update: ${isLoading}`);
      items = querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      isLoading = false; // Set loading false AFTER data is processed
      error = null;
      console.log(`[${executionCount}] items updated (count: ${items.length}), isLoading set to false.`);
    }, (err) => {
      console.error(`[${executionCount}] Error in Firestore listener: `, err);
      error = "Failed to load items. Check console for details.";
      isLoading = false; // Also set loading false on error
      console.log(`[${executionCount}] Error occurred, isLoading set to false.`);
    });
    console.log(`[${executionCount}] New listener subscribed.`);
  }

  // Reactive statement: when showOnlyPending changes, re-setup the subscription.
  $: {
    console.log(`Reactive block triggered. showOnlyPending: ${showOnlyPending}`);
    setupSubscription(showOnlyPending);
  }

  onDestroy(() => {
    console.log("onDestroy: Cleaning up Firestore listener.");
    if (currentUnsubscribeFn) {
      currentUnsubscribeFn();
    }
  });

  async function updateItemStatus(itemId, newStatus) {
    console.log(`updateItemStatus called for item ${itemId} to ${newStatus}`);
    const itemRef = doc(db, collectionName, itemId);
    const updateData = { status: newStatus };

    if (newStatus === 'approved') {
      updateData.approvedBy = 'system'; 
      updateData.approvedAt = serverTimestamp();
      updateData.rejectedBy = null; 
      updateData.rejectedAt = null;
    } else if (newStatus === 'rejected') {
      updateData.rejectedBy = 'system'; 
      updateData.rejectedAt = serverTimestamp();
      updateData.approvedBy = null;
      updateData.approvedAt = null;
    } else if (newStatus === 'pending') { 
        updateData.approvedBy = null;
        updateData.approvedAt = null;
        updateData.rejectedBy = null;
        updateData.rejectedAt = null;
    }

    try {
      await updateDoc(itemRef, updateData);
      console.log(`Item ${itemId} status successfully updated to ${newStatus}`);
    } catch (e) {
      console.error(`Error updating item ${itemId} to ${newStatus}: `, e);
      error = `Failed to update item to ${newStatus}. Check console.`;
    }
  }

  // Helper to display object data nicely
  function prettyPrint(obj) {
    if (obj === null || obj === undefined) return '';
    return Object.entries(obj)
      .map(([key, value]) => {
        if (typeof value === 'object' && value !== null) {
          if (value.toDate && typeof value.toDate === 'function') {
            return `${key}: ${value.toDate().toLocaleString()}`;
          }
          return `${key}: ${JSON.stringify(value)}`;
        }
        return `${key}: ${value}`;
      })
      .join(', ');
  }

  function formatRelativeTime(timestamp) {
    if (!timestamp || typeof timestamp.toDate !== 'function') {
      return 'Unknown date';
    }
    const date = timestamp.toDate();
    const now = new Date();
    const seconds = Math.round((now - date) / 1000);
    const minutes = Math.round(seconds / 60);
    const hours = Math.round(minutes / 60);
    const days = Math.round(hours / 24);
    const weeks = Math.round(days / 7);
    const months = Math.round(days / 30.44); // Average days in month
    const years = Math.round(days / 365.25); // Account for leap year

    if (seconds < 5) return 'just now';
    if (seconds < 60) return `${seconds} seconds ago`;
    if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (days < 7) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (weeks < 5) return `${weeks} week${weeks > 1 ? 's' : ''} ago`; // Up to 4 weeks
    if (months < 12) return `${months} month${months > 1 ? 's' : ''} ago`;
    return `${years} year${years > 1 ? 's' : ''} ago`;
  }
</script>

<main class="container mt-4">
  <h1 class="mb-4">Approvals Viewer</h1>

  <div class="form-check mb-3">
    <input class="form-check-input" type="checkbox" id="showPendingToggle" bind:checked={showOnlyPending}>
    <label class="form-check-label" for="showPendingToggle">
      Show only pending
    </label>
  </div>

  {#if isLoading}
    <div class="d-flex justify-content-center">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
  {:else if error}
    <div class="alert alert-danger" role="alert">
      {error}
    </div>
  {:else if items.length === 0}
    <p class="text-muted">No items found matching your criteria.</p>
  {:else}
    <ul class="list-group">
      {#each items as item (item.id)}
        <li class="list-group-item">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h5 class="mb-1">{item.itemName || 'No Item Name'}</h5>
              <small class="text-muted">Amount: ${item.amount !== undefined ? item.amount.toLocaleString() : 'N/A'}</small><br>
              <small class="text-muted">Requested by: {item.requestedBy || 'N/A'} &bull; {formatRelativeTime(item.requestedAt)}</small><br>
            </div>
            <div class="ms-3">
              {#if item.status === 'pending'}
                <button class="btn btn-success btn-sm me-2 mb-1" on:click={() => updateItemStatus(item.id, 'approved')}>Approve</button>
                <button class="btn btn-danger btn-sm mb-1" on:click={() => updateItemStatus(item.id, 'rejected')}>Deny</button>
              {:else if item.status === 'approved'}
                <button class="btn btn-warning btn-sm mb-1" on:click={() => updateItemStatus(item.id, 'pending')}>Re-Open</button> <!-- Or Deny -->
                <button class="btn btn-danger btn-sm mb-1" on:click={() => updateItemStatus(item.id, 'rejected')}>Deny</button>
              {:else if item.status === 'rejected'}
                <button class="btn btn-warning btn-sm mb-1" on:click={() => updateItemStatus(item.id, 'pending')}>Re-Open</button> <!-- Or Approve -->
                <button class="btn btn-success btn-sm mb-1" on:click={() => updateItemStatus(item.id, 'approved')}>Approve</button>
              {/if}
            </div>
          </div>
        </li>
      {/each}
    </ul>
  {/if}
</main>

<style>
  main {
    max-width: 800px;
    margin: 0 auto;
  }
  .list-group-item h5 {
    color: #0d6efd; /* Bootstrap primary blue */
  }
  .spinner-border {
    width: 3rem;
    height: 3rem;
  }
  /* Add any additional global or component-specific styles here */
  /* You can also leverage Bootstrap utility classes directly in your HTML */
</style>