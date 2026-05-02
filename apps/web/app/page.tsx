import { redirect } from "next/navigation"

export default function HomePage() {
  redirect("/workspace") // CRG: Make the workflow workspace the default entry point.
}
