# just-notifications

A simple and lightweight notification system for managing and displaying notifications in your applications.

## Features

- ✨ Simple and intuitive API
- 🎯 Easy-to-use notification management
- 🔔 Customizable notification types
- 📦 Lightweight and dependency-free
- 🚀 Fast and efficient

## Installation

```bash
npm install just-notifications
```

Or with yarn:

```bash
yarn add just-notifications
```

## Usage

### Basic Example

```javascript
import { Notifications } from 'just-notifications';

const notifications = new Notifications();

// Add a notification
notifications.add({
  id: 'notif-1',
  title: 'Success',
  message: 'Operation completed successfully',
  type: 'success'
});

// Get all notifications
const allNotifications = notifications.getAll();

// Remove a notification
notifications.remove('notif-1');
```

## API Documentation

### Constructor

```javascript
new Notifications(options?: NotificationOptions)
```

### Methods

#### `add(notification: Notification): void`
Adds a new notification to the queue.

#### `remove(id: string): void`
Removes a notification by its ID.

#### `getAll(): Notification[]`
Returns all current notifications.

#### `clear(): void`
Clears all notifications.

## Notification Types

- `success` - For successful operations
- `error` - For error messages
- `warning` - For warning messages
- `info` - For informational messages

## Configuration

You can customize the behavior of notifications:

```javascript
const notifications = new Notifications({
  maxNotifications: 5,
  autoRemove: true,
  timeout: 5000
});
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you have any questions or issues, please open an issue on the GitHub repository.
