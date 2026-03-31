import { redirect } from "next/navigation";

export default function AuthDemoPage() {
  redirect("/auth/login");
}
