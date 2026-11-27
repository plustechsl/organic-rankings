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
  role: string;
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

export type VerificationStatus = "fiable" | "dudoso";

export type ReportReason =
  | "sin_fecha"
  | "sin_autor"
  | "fuente_dudosa"
  | "datos_contradictorios"
  | "otro";

export const REPORT_REASONS: ReportReason[] = [
  "sin_fecha",
  "sin_autor",
  "fuente_dudosa",
  "datos_contradictorios",
  "otro",
];

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
  report_count: number;
  verification_status: VerificationStatus | null;
  verified_at: string | null;
  verified_by: string | null;
  created_at: string;
  updated_at: string;
};

export type ReportResponse = {
  link_id: number;
  reason: ReportReason;
  report_count: number;
};

export type ReportDetail = {
  id: number;
  user_id: number;
  username: string | null;
  reason: ReportReason;
  created_at: string;
};

export type AdminLinkReport = {
  link_id: number;
  title: string;
  url: string;
  report_count: number;
  last_reported_at: string;
  verification_status: VerificationStatus | null;
  verified_at: string | null;
  reports: ReportDetail[];
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
  sensitivity: Sensitivity;
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

export type AiUrlCheckResult = {
  url: string;
  enough_text: boolean;
  min_words: number;
  score: number | null;
  label: "bajo" | "mixto" | "alto" | null;
  words: number;
  confidence: number | null;
  signals: Record<string, number | null>;
};
