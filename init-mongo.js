// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

// Switch to the hill_ts database
db = db.getSiblingDB('hill_ts');

// Create collections if they don't exist
db.createCollection('users');
db.createCollection('projects');
db.createCollection('templates');
db.createCollection('folders');
db.createCollection('files');
db.createCollection('labels');

// Create indexes for better performance
db.users.createIndex({ "mail": 1 }, { unique: true });
db.projects.createIndex({ "projectName": 1 });
db.templates.createIndex({ "templateName": 1 });
db.folders.createIndex({ "name": 1 });
db.files.createIndex({ "name": 1 });
db.files.createIndex({ "parsing": 1 }); // For worker queries
db.labels.createIndex({ "events": 1 });

print('MongoDB initialization completed successfully!');
