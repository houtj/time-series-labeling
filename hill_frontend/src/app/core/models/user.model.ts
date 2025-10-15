import { BaseModel, MongoDate } from './common.model';

/**
 * User profile from authentication provider (e.g., Microsoft Graph)
 */
export interface UserProfile {
  displayName?: string;
  givenName?: string;
  surname?: string;
  userPrincipalName?: string;
  id?: string;
  mail?: string;
}

/**
 * Contribution history entry
 */
export interface ContributionHistory {
  time: string;
  nbEventsLabeled: number;
}

/**
 * Recent item access entry
 */
export interface RecentItem {
  folder: string;
  file: string;
  displayText: string;
}

/**
 * User message/notification
 */
export interface UserMessage {
  folder: string;
  file: string;
  project: string;
  displayText: string;
}

/**
 * User model representing a registered user in the system
 */
export interface UserModel extends BaseModel {
  name: string;
  activeSince: MongoDate;
  folderList: string[];
  projectList: string[];
  contributionHistory: ContributionHistory[];
  recent: RecentItem[];
  message: UserMessage[];
  badge: string;
  mail: string;
  rank: number;
}


