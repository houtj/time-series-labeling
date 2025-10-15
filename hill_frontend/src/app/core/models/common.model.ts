/**
 * Common types used across the application
 */

/**
 * MongoDB ObjectId representation
 */
export interface MongoId {
  $oid: string;
}

/**
 * MongoDB Date representation
 */
export interface MongoDate {
  $date: string;
}

/**
 * Base model interface for entities with MongoDB IDs
 */
export interface BaseModel {
  _id?: MongoId;
}


