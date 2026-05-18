import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  // CRG: Buttons keep existing variants but move to the polished UI type role.
  "lux-button-type inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 disabled:pointer-events-none disabled:opacity-45 active:translate-y-px",
  {
    variants: {
      variant: {
        // CRG: Preserve existing variant names while moving the visual system to luxury SaaS surfaces.
        default:
          "bg-primary text-primary-foreground shadow-[0_18px_36px_hsl(var(--primary)/0.18)] hover:bg-primary/92 hover:shadow-[0_20px_44px_hsl(var(--primary)/0.24)]",
        primary:
          "bg-primary text-primary-foreground shadow-[0_18px_36px_hsl(var(--primary)/0.18)] hover:bg-primary/92",
        secondary:
          "border border-border/70 bg-secondary/80 text-secondary-foreground shadow-sm hover:border-primary/25 hover:bg-secondary",
        outline:
          "border border-border/80 bg-card/50 text-foreground shadow-sm backdrop-blur hover:border-primary/35 hover:bg-card",
        ghost:
          "text-muted-foreground hover:bg-secondary/70 hover:text-foreground",
        link:
          "h-auto rounded-none px-0 text-primary underline-offset-4 hover:underline",
        destructive:
          "bg-destructive text-destructive-foreground shadow-[0_18px_36px_hsl(var(--destructive)/0.18)] hover:bg-destructive/90",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-lg px-3 text-xs",
        lg: "h-12 rounded-2xl px-6 text-base",
        icon: "h-10 w-10 p-0",
        "icon-sm": "h-8 w-8 rounded-lg p-0",
        "icon-lg": "h-12 w-12 rounded-2xl p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  isLoading?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, isLoading = false, disabled, children, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    if (asChild) {
      return (
        <Comp ref={ref} className={cn(buttonVariants({ variant, size, className }))} {...props}>
          {/* CRG: Radix Slot requires exactly one child; loaders stay on native buttons only. */}
          {children}
        </Comp>
      )
    }
    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size, className }))}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : null}
        {children}
      </Comp>
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
