export type Category = {
  id: number;
  name: string;
  slug: string;
  tags: string[];
  created_at: string;
  updated_at: string;
};

export type LinkList = {
  id: number;
  user_id: number;
  username: string | null;
  title: string;
  slug: string;
  description: string | null;
  image_url: string | null;
  points: number;
  category_id: number;
  created_at: string;
  updated_at: string;
};

export type PublicUser = {
  id: number;
  username: string;
  created_at: string;
  aura: number;
};

export type PublicUserProfile = PublicUser & {
  lists: LinkList[];
};

export type InvitationStatus = "pending" | "approved" | "rejected";

export type ReferralInvite = {
  id: number;
  user_id: number;
  username: string | null;
  status: InvitationStatus;
  points: number;
  created_at: string;
  reviewed_at: string | null;
};

export type MyReferrals = {
  code: string;
  points: number;
  points_per_invite: number;
  invited: ReferralInvite[];
};

export type AdminInvitation = {
  id: number;
  inviter_id: number;
  inviter_username: string | null;
  invited_user_id: number;
  invited_username: string | null;
  status: InvitationStatus;
  points: number;
  created_at: string;
  reviewed_at: string | null;
};

export type Sensitivity = "none" | "adult" | "violence";

export type Link = {
  id: number;
  list_id: number;
  user_id: number;
  username: string | null;
  title: string;
  url: string;
  description: string | null;
  image_url: string | null;
  points: number;
  sensitivity: Sensitivity;
  ai_score: number | null;
  ai_checked_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Tag = {
  id: number;
  name: string;
  slug: string;
  created_at: string;
};

export type LinkPreview = {
  title: string | null;
  description: string | null;
  tags: string[];
  belongs: boolean;
  reason: string;
  category: string | null;
};

export type LinkRequestStatus = "pending" | "approved" | "rejected";

export type LinkRequest = {
  id: number;
  list_id: number;
  user_id: number;
  username: string | null;
  title: string;
  url: string;
  description: string | null;
  tags: string[];
  sensitivity: Sensitivity;
  status: LinkRequestStatus;
  created_at: string;
  reviewed_at: string | null;
  reviewed_by: number | null;
  reviewer_username: string | null;
  link_id?: number | null;
};

export type SearchResult = {
  id: number;
  title: string;
  url: string;
  description: string;
  points: number;
  sensitivity: Sensitivity;
  created_at: string;
  list_id: number;
  list_title: string | null;
  category_id: number | null;
  category_name: string | null;
  tags: string[];
};

export type SearchResponse = {
  query: string | null;
  total: number;
  page: number;
  page_size: number;
  results: SearchResult[];
};
