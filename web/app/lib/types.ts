export type Category = {
  id: number;
  name: string;
  slug: string;
  parent_id: number | null;
  created_at: string;
  updated_at: string;
  children?: Category[];
};

export type LinkList = {
  id: number;
  user_id: number;
  title: string;
  slug: string;
  description: string | null;
  image_url: string | null;
  points: number;
  category_id: number;
  subcategory_id: number | null;
  created_at: string;
  updated_at: string;
};

export type Link = {
  id: number;
  list_id: number;
  user_id: number;
  title: string;
  url: string;
  description: string | null;
  image_url: string | null;
  points: number;
  created_at: string;
  updated_at: string;
};

export type Tag = {
  id: number;
  name: string;
  slug: string;
  created_at: string;
};

export type SearchResult = {
  id: number;
  title: string;
  url: string;
  description: string;
  points: number;
  created_at: string;
  list_id: number;
  list_title: string | null;
  category_id: number | null;
  category_name: string | null;
  subcategory_id: number | null;
  subcategory_name: string | null;
  tags: string[];
};

export type SearchResponse = {
  query: string | null;
  total: number;
  page: number;
  page_size: number;
  results: SearchResult[];
};
