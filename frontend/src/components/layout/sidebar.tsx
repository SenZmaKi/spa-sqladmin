import React from 'react'
import { Link, useRouterState } from '@tanstack/react-router'
import { cn } from '@/lib/utils'
import { getBaseUrl, logout } from '@/lib/api'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { useUIStore } from '@/stores/ui-store'
import type { MenuItem, SiteData } from '@/lib/types'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyLinkTo = any
import {
  // Original imports
  Users,
  Package,
  LayoutDashboard,
  Settings,
  FileText,
  ShoppingCart,
  Tag,
  Mail,
  Globe,
  Image,
  MessageSquare,
  Calendar,
  Database,
  Shield,
  Star,
  Heart,
  BookOpen,
  Folder,
  Home,
  Bell,
  Map,
  CreditCard,
  Truck,
  ChevronDown,
  ChevronRight,
  PanelLeftClose,
  PanelLeft,
  LogOut,
  // Expanded icon set
  Activity,
  AlertCircle,
  AlertTriangle,
  Archive,
  Award,
  BarChart,
  BarChart2,
  BarChart3,
  Bookmark,
  Box,
  Briefcase,
  Building,
  Building2,
  Camera,
  Check,
  CheckCircle,
  Circle,
  Clipboard,
  Clock,
  Cloud,
  Code,
  Cog,
  Compass,
  Copy,
  DollarSign,
  Download,
  Edit,
  Eye,
  EyeOff,
  File,
  Film,
  Filter,
  Flag,
  Gift,
  Hash,
  Headphones,
  HelpCircle,
  Inbox,
  Info,
  Key,
  Layers,
  Layout,
  Link as LinkIcon,
  List,
  Lock,
  LogIn,
  MapPin,
  Megaphone,
  Menu,
  Mic,
  Monitor,
  Moon,
  MoreHorizontal,
  Music,
  Navigation,
  Paperclip,
  Pen,
  Phone,
  PieChart,
  Pin,
  Play,
  Plus,
  Printer,
  Radio,
  RefreshCw,
  Repeat,
  Rocket,
  RotateCw,
  Rss,
  Save,
  Scissors,
  Search,
  Send,
  Server,
  Share,
  ShieldCheck,
  Smartphone,
  Speaker,
  Sun,
  Table,
  Target,
  Terminal,
  ThumbsUp,
  ThumbsDown,
  Hammer,
  Trash,
  Trash2,
  TrendingUp,
  TrendingDown,
  Upload,
  User,
  UserCheck,
  UserPlus,
  UserX,
  Video,
  Wallet,
  Wifi,
  Wrench,
  X,
  Zap,
  ZoomIn,
  ZoomOut,
  GitBranch,
  GitCommit,
  GitMerge,
  GitPullRequest,
  Github,
  Cpu,
  HardDrive,
  MemoryStick,
  Plug,
  Power,
  QrCode,
  Scan,
  Usb,
  Car,
  Bike,
  Bus,
  Plane,
  Ship,
  Train,
  type LucideIcon,
} from 'lucide-react'


const LUCIDE_BY_NAME: Record<string, LucideIcon> = {
  // Original set
  Users, Package, Settings, FileText, ShoppingCart, Tag, Mail, Globe, Image,
  MessageSquare, Calendar, Database, Shield, Star, Heart, BookOpen, Folder,
  Home, Bell, Map, CreditCard, Truck, LayoutDashboard,
  // Expanded set
  Activity, AlertCircle, AlertTriangle, Archive, Award,
  BarChart, BarChart2, BarChart3,
  Bookmark, Box, Briefcase, Building, Building2, Camera, Check, CheckCircle,
  Circle, Clipboard, Clock, Cloud, Code, Cog, Compass, Copy,
  DollarSign, Download, Edit, Eye, EyeOff, File, Film, Filter,
  Flag, Gift, Hash, Headphones, HelpCircle, Inbox, Info, Key,
  Layers, Layout, Link: LinkIcon, List, Lock, LogIn, LogOut, MapPin,
  Megaphone, Menu, Mic, Monitor, Moon, MoreHorizontal, Music, Navigation,
  Paperclip, Pen, Phone, PieChart, Pin, Play, Plus, Printer,
  Radio, RefreshCw, Repeat, Rocket, RotateCw, Rss, Save, Scissors,
  Search, Send, Server, Share, ShieldCheck, Smartphone, Speaker, Sun,
  Table, Target, Terminal, ThumbsUp, ThumbsDown, Hammer, Trash, Trash2,
  TrendingUp, TrendingDown, Upload, User, UserCheck, UserPlus, UserX, Video,
  Wallet, Wifi, Wrench, X, Zap, ZoomIn, ZoomOut,
  GitBranch, GitCommit, GitMerge, GitPullRequest, Github,
  Cpu, HardDrive, MemoryStick, Plug, Power, QrCode, Scan, Usb,
  Car, Bike, Bus, Plane, Ship, Train,
}

// --- SVG string support ---

function isSvgString(icon: string): boolean {
  return icon.trim().startsWith('<svg')
}

export function SvgIcon({ svg, className }: { svg: string; className?: string }) {
  const processedSvg = svg.replace(/<svg/, `<svg class="${className || 'h-4 w-4'}"`)
  return <span dangerouslySetInnerHTML={{ __html: processedSvg }} />
}

export type ResolvedIcon =
  | { type: 'lucide'; icon: LucideIcon }
  | { type: 'svg'; svg: string }

export function resolveIcon(icon: string): ResolvedIcon {
  if (!icon) return { type: 'lucide', icon: LayoutDashboard }
  if (isSvgString(icon)) return { type: 'svg', svg: icon }
  if (LUCIDE_BY_NAME[icon]) return { type: 'lucide', icon: LUCIDE_BY_NAME[icon] }
  const lower = icon.toLowerCase()
  for (const [name, comp] of Object.entries(LUCIDE_BY_NAME)) {
    if (name.toLowerCase() === lower) return { type: 'lucide', icon: comp }
  }
  return { type: 'lucide', icon: LayoutDashboard }
}

interface SidebarProps {
  site: SiteData
  collapsed: boolean
  onCollapsedChange: (collapsed: boolean) => void
  mobileOpen: boolean
  onMobileClose: () => void
}

export function Sidebar({
  site,
  collapsed,
  onCollapsedChange,
  mobileOpen,
  onMobileClose,
}: SidebarProps) {
  const baseUrl = getBaseUrl()
  const routerState = useRouterState()
  const [showLogoutDialog, setShowLogoutDialog] = React.useState(false)
  // Tanstack Router strips basepath from location.pathname,
  // so we use the full browser URL for active-state matching.
  const currentPath = window.location.pathname

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onMobileClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex flex-col border-r bg-card transition-all duration-300',
          collapsed ? 'w-16' : 'w-64',
          'lg:translate-x-0',
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Logo / Title */}
        <div className="flex h-14 items-center border-b px-4">
          {site.logo_url ? (
            <Link
              to={'/' as AnyLinkTo}
              onClick={onMobileClose}
              className={cn(
                'flex items-center gap-2 font-semibold text-foreground',
                collapsed ? 'justify-center w-full' : ''
              )}
            >
              <img
                src={site.logo_url}
                alt={site.title}
                className="h-8 object-contain shrink-0"
              />
              {!collapsed && <span className="truncate">{site.title}</span>}
            </Link>
          ) : (
            <Link
              to={'/' as AnyLinkTo}
              onClick={onMobileClose}
              className={cn(
                'flex items-center gap-2 font-semibold text-foreground',
                collapsed ? 'justify-center w-full' : ''
              )}
            >
              <LayoutDashboard className="h-5 w-5 shrink-0" />
              {!collapsed && <span className="truncate">{site.title}</span>}
            </Link>
          )}
        </div>

        {/* Menu */}
        <nav className="flex-1 overflow-y-auto py-2">
          {site.menu.map((item, i) => (
            <SidebarMenuItem
              key={`${item.name}-${i}`}
              item={item}
              collapsed={collapsed}
              currentPath={currentPath}
              baseUrl={baseUrl}
              onNavigate={onMobileClose}
            />
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t p-2">
          {site.has_auth && (
            <>
              <Button
                variant="ghost"
                className={cn(
                  'w-full justify-start text-muted-foreground hover:text-foreground',
                  collapsed ? 'justify-center px-0' : ''
                )}
                onClick={() => setShowLogoutDialog(true)}
              >
                <LogOut className="h-4 w-4 shrink-0" />
                {!collapsed && <span>Logout</span>}
              </Button>
              <Dialog open={showLogoutDialog} onOpenChange={setShowLogoutDialog}>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Sign out</DialogTitle>
                    <DialogDescription>
                      Are you sure you want to sign out?
                    </DialogDescription>
                  </DialogHeader>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setShowLogoutDialog(false)}>
                      Cancel
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={async () => {
                        setShowLogoutDialog(false)
                        await logout()
                        window.location.href = `${baseUrl}/login`
                      }}
                    >
                      Sign out
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </>
          )}
          <Button
            variant="ghost"
            className={cn(
              'w-full justify-start text-muted-foreground hover:text-foreground',
              collapsed ? 'justify-center px-0' : ''
            )}
            onClick={() => onCollapsedChange(!collapsed)}
          >
            {collapsed ? (
              <PanelLeft className="h-4 w-4 shrink-0" />
            ) : (
              <>
                <PanelLeftClose className="h-4 w-4 shrink-0" />
                <span>Collapse</span>
              </>
            )}
          </Button>
        </div>
      </aside>
    </>
  )
}

function SidebarMenuItem({
  item,
  collapsed,
  currentPath,
  baseUrl,
  depth = 0,
  onNavigate,
}: {
  item: MenuItem
  collapsed: boolean
  currentPath: string
  baseUrl: string
  depth?: number
  onNavigate: () => void
}) {
  const [expanded, setExpanded] = React.useState(true)
  const resolved = resolveIcon(item.icon)

  if (item.type === 'category') {
    if (collapsed) {
      return (
        <>
          {item.children?.map((child, i) => (
            <SidebarMenuItem
              key={`${child.name}-${i}`}
              item={child}
              collapsed={collapsed}
              currentPath={currentPath}
              baseUrl={baseUrl}
              depth={depth}
              onNavigate={onNavigate}
            />
          ))}
        </>
      )
    }

    return (
      <div className="mt-2">
        <button
          className="flex w-full items-center gap-2 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? (
            <ChevronDown className="h-3 w-3" />
          ) : (
            <ChevronRight className="h-3 w-3" />
          )}
          <span>{item.name}</span>
        </button>
        {expanded && (
          <div>
            {item.children?.map((child, i) => (
              <SidebarMenuItem
                key={`${child.name}-${i}`}
                item={child}
                collapsed={collapsed}
                currentPath={currentPath}
                baseUrl={baseUrl}
                depth={depth + 1}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  const href = item.identity ? `/${item.identity}/list` : '/'
  const identityPrefix = item.identity ? `${baseUrl}/${item.identity}` : null
  const isActive =
    identityPrefix
      ? currentPath === identityPrefix ||
        currentPath.startsWith(`${identityPrefix}/`)
      : currentPath === baseUrl || currentPath === `${baseUrl}/`

  return (
    <Link
      to={href as AnyLinkTo}
      onClick={onNavigate}
      className={cn(
        'flex items-center gap-3 rounded-md mx-2 px-3 py-2 text-sm font-medium transition-colors',
        isActive
          ? 'bg-primary/10 text-primary'
          : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
        collapsed ? 'justify-center px-2' : '',
        depth > 0 && !collapsed ? 'ml-4' : ''
      )}
      title={collapsed ? item.name : undefined}
    >
      {resolved.type === 'lucide' ? (
        <resolved.icon className="h-4 w-4 shrink-0" />
      ) : (
        <SvgIcon svg={resolved.svg} className="h-4 w-4 shrink-0" />
      )}
      {!collapsed && <span className="truncate">{item.name}</span>}
    </Link>
  )
}

