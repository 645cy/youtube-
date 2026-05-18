/**
 * 全局 Toast 通知工具
 * 通过 CustomEvent 与 ClientLayout 中的 Toast 系统通信
 */

export type ToastType = "success" | "error" | "warning" | "info"

export function toast(type: ToastType, message: string, duration = 3000) {
  if (typeof window === "undefined") return
  window.dispatchEvent(
    new CustomEvent("api-toast", {
      detail: { type, message, duration },
    })
  )
}

export function toastSuccess(message: string) {
  toast("success", message)
}

export function toastError(message: string) {
  toast("error", message)
}

export function toastWarning(message: string) {
  toast("warning", message)
}

export function toastInfo(message: string) {
  toast("info", message)
}
