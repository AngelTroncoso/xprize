import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import Sidebar from "./Sidebar";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  // Fetch profile to get full_name
  const { data: profile } = await supabase
    .from("profiles")
    .select("full_name, grade_level")
    .eq("id", user.id)
    .single();

  return (
    <div className="min-h-screen bg-[#020208] flex">
      <Sidebar
        userName={profile?.full_name ?? user.email?.split("@")[0] ?? "Usuario"}
        userEmail={user.email ?? ""}
      />
      <main className="flex-1 overflow-auto p-8">{children}</main>
    </div>
  );
}