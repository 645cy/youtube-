import * as React from "react"
import * as ToastPrimitive from "@radix-ui/react-toast"
import { AlertCircle, CheckCircle, Info, X } from "lucide-react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const ToastProvider = ToastPrimitive.Provider

const ToastViewport = React.forwardRef<
  React.ElementRef<typeof ToastPrimitive.Viewport>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Viewport>
>(({ className, ...props }, ref) => (
  <ToastPrimitive.Viewport
    ref={ref}
    className={cn("fixed right-4 top-4 z-[100] flex max-h-screen w-[min(420px,calc(100vw-2rem))] flex-col gap-2", className)}
    {...props}
  />
))
ToastViewport.displayName = ToastPrimitive.Viewport.displayName

const toastVariants = cva(
  "group pointer-events-auto relative flex w-full items-start gap-3 overflow-hidden rounded-xl border bg-card/95 p-4 pr-10 text-foreground shadow-2xl backdrop-blur-xl transition-all",
  {
    variants: {
      variant: {
        // CRG: Toast states use subtle premium color, not saturated alert blocks.
        default: "border-border/80",
        success: "border-emerald-500/25 text-emerald-500",
        error: "border-red-500/25 text-red-500",
        warning: "border-amber-500/25 text-amber-500",
        info: "border-sky-500/25 text-sky-500",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

const Toast = React.forwardRef<
  React.ElementRef<typeof ToastPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Root> & VariantProps<typeof toastVariants>
>(({ className, variant, ...props }, ref) => (
  <ToastPrimitive.Root ref={ref} className={cn(toastVariants({ variant }), className)} {...props} />
))
Toast.displayName = ToastPrimitive.Root.displayName

const ToastAction = React.forwardRef<
  React.ElementRef<typeof ToastPrimitive.Action>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Action>
>(({ className, ...props }, ref) => (
  <ToastPrimitive.Action
    ref={ref}
    className={cn("inline-flex h-8 items-center justify-center rounded-lg border border-border/80 px-3 text-sm font-semibold hover:bg-secondary", className)}
    {...props}
  />
))
ToastAction.displayName = ToastPrimitive.Action.displayName

const ToastClose = React.forwardRef<
  React.ElementRef<typeof ToastPrimitive.Close>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Close>
>(({ className, ...props }, ref) => (
  <ToastPrimitive.Close
    ref={ref}
    className={cn("absolute right-3 top-3 rounded-lg p-1 text-muted-foreground opacity-0 transition hover:bg-secondary hover:text-foreground group-hover:opacity-100", className)}
    toast-close=""
    {...props}
  >
    <X className="h-4 w-4" />
  </ToastPrimitive.Close>
))
ToastClose.displayName = ToastPrimitive.Close.displayName

const ToastTitle = React.forwardRef<
  React.ElementRef<typeof ToastPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Title>
>(({ className, ...props }, ref) => (
  <ToastPrimitive.Title ref={ref} className={cn("text-sm font-bold text-foreground", className)} {...props} />
))
ToastTitle.displayName = ToastPrimitive.Title.displayName

const ToastDescription = React.forwardRef<
  React.ElementRef<typeof ToastPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Description>
>(({ className, ...props }, ref) => (
  <ToastPrimitive.Description ref={ref} className={cn("text-sm leading-6 text-muted-foreground", className)} {...props} />
))
ToastDescription.displayName = ToastPrimitive.Description.displayName

const ToastIcon = ({ variant }: { variant?: string }) => {
  if (variant === "success") return <CheckCircle className="h-5 w-5 shrink-0 text-emerald-500" />
  if (variant === "error" || variant === "warning") return <AlertCircle className="h-5 w-5 shrink-0" />
  return <Info className="h-5 w-5 shrink-0 text-sky-500" />
}

interface ToastData {
  id: string
  type: "success" | "error" | "warning" | "info"
  title: string
  message: string
}

export { ToastProvider, ToastViewport, Toast, ToastTitle, ToastDescription, ToastClose, ToastAction, ToastIcon, type ToastData }
