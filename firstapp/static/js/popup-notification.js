// Popup Notification System
function showNotification(message, type = 'success') {
  // Create notification container if it doesn't exist
  let container = document.getElementById('notification-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'notification-container';
    document.body.appendChild(container);
  }

  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.innerHTML = `
    <div class="notification-content">
      <span class="notification-message">${message}</span>
      <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
    </div>
  `;

  // Add to container
  container.appendChild(notification);

  // Auto-remove after 4 seconds
  setTimeout(() => {
    notification.classList.add('notification-fade-out');
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 4000);
}
