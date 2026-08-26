import {
  Activity,
  Box,
  CheckCircle2,
  FileCheck2,
  GitBranch,
  Home,
  Inbox,
  Settings,
  ShieldCheck,
} from "lucide-react";

export const navItems = [
  ["Inbox", Inbox],
  ["Overview", Home],
  ["Sources", Box],
  ["Workflows", GitBranch],
  ["Approvals", CheckCircle2],
  ["Activity", Activity],
  ["Settings", Settings],
];

export const artifactIcons = [FileCheck2, ShieldCheck, Activity, GitBranch];
