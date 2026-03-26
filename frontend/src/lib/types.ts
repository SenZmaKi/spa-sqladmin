export interface AdminConfig {
  baseUrl: string
  apiUrl: string
  title?: string
  logoUrl?: string | null
  faviconUrl?: string | null
  colorPalette?: ColorPalette | null
}

export interface ColorPalette {
  light?: Record<string, string>
  dark?: Record<string, string>
}

export interface ModelInfo {
  identity: string
  name: string
  name_plural: string
  icon: string
  permissions: Permissions
}

export interface Permissions {
  can_create: boolean
  can_edit: boolean
  can_delete: boolean
  can_view_details: boolean
  can_export: boolean
}

export interface MenuItem {
  type: 'category' | 'item'
  name: string
  icon: string
  identity?: string
  is_model?: boolean
  children?: MenuItem[]
}

export interface SiteData {
  title: string
  logo_url: string | null
  favicon_url: string | null
  color_palette: ColorPalette | null
  base_url: string
  models: ModelInfo[]
  menu: MenuItem[]
  has_auth: boolean
}

export interface ColumnDef {
  name: string
  label: string
  sortable: boolean
  is_relation: boolean
}

export interface FilterDef {
  name: string
  title: string
  has_operator: boolean
  options?: [string, string][]
  operations?: [string, string][]
}

export interface RelationValue {
  pk: string
  repr: string
  identity: string
}

export interface ListData {
  rows: Record<string, any>[]
  columns: ColumnDef[]
  page: number
  page_size: number
  count: number
  page_size_options: number[]
  searchable: boolean
  search_placeholder: string
  filters: FilterDef[]
  actions_in_list: Record<string, string>
  actions_in_detail: Record<string, string>
  action_confirmations: Record<string, string>
  export_types: string[]
  permissions: Permissions
  name: string
  name_plural: string
  identity: string
}

export interface DetailField {
  name: string
  label: string
  value: any
  is_relation: boolean
  related?: RelationValue | RelationValue[]
}

export interface DetailData {
  fields: DetailField[]
  pk: string
  repr: string
  permissions: { can_edit: boolean; can_delete: boolean }
  actions: Record<string, string>
  action_confirmations: Record<string, string>
  name: string
  identity: string
}

export interface FormFieldOption {
  value: string
  label: string
}

export interface FormFieldDef {
  name: string
  label: string
  type: string
  required: boolean
  value: any
  description: string
  options?: FormFieldOption[]
  ajax_url?: string
  value_label?: string
  widget_args?: Record<string, any>
}

export interface FormSchema {
  fields: FormFieldDef[]
  save_as: boolean
  save_as_continue: boolean
  identity: string
  name: string
  pk: string | null
}

export interface AuthStatus {
  authenticated: boolean
  has_auth: boolean
}
