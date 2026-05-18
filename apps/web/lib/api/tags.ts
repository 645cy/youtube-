import { requestWithRetry } from "./request"

export interface TagItem {
  name: string
  count: number
  trend: "up" | "down" | "stable"
}

export const tagApi = {
  list: () => requestWithRetry<TagItem[]>("/api/v1/channels/tags"),
}
