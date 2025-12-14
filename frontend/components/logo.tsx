"use client"

import Image from "next/image"
import { cn } from "@/lib/utils"

interface LogoProps {
  className?: string
  showText?: boolean
  size?: "sm" | "md" | "lg"
  variant?: "light" | "dark"
}

export function Logo({ className, showText = false, size = "md", variant = "dark" }: LogoProps) {
  const sizeClasses = {
    sm: "w-20 h-20",
    md: "w-28 h-28",
    lg: "w-40 h-40"
  }

  const imageSizes = {
    sm: { width: 80, height: 80 },
    md: { width: 112, height: 112 },
    lg: { width: 160, height: 160 }
  }

  return (
    <div className={cn("flex items-center justify-center", className)}>
      {/* Logo Revenux avec symbole infini uniquement */}
      <div className={cn("relative flex items-center justify-center", sizeClasses[size])}>
        <Image
          src="/logo.png"
          alt="Revenux Logo"
          width={imageSizes[size].width}
          height={imageSizes[size].height}
          className="object-contain w-full h-full"
          priority
        />
      </div>
    </div>
  )
}

import Image from "next/image"
import { cn } from "@/lib/utils"

interface LogoProps {
  className?: string
  showText?: boolean
  size?: "sm" | "md" | "lg"
  variant?: "light" | "dark"
}

export function Logo({ className, showText = false, size = "md", variant = "dark" }: LogoProps) {
  const sizeClasses = {
    sm: "w-20 h-20",
    md: "w-28 h-28",
    lg: "w-40 h-40"
  }

  const imageSizes = {
    sm: { width: 80, height: 80 },
    md: { width: 112, height: 112 },
    lg: { width: 160, height: 160 }
  }

  return (
    <div className={cn("flex items-center justify-center", className)}>
      {/* Logo Revenux avec symbole infini uniquement */}
      <div className={cn("relative flex items-center justify-center", sizeClasses[size])}>
        <Image
          src="/logo.png"
          alt="Revenux Logo"
          width={imageSizes[size].width}
          height={imageSizes[size].height}
          className="object-contain w-full h-full"
          priority
        />
      </div>
    </div>
  )
}
