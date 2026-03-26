import {
  createRouter,
  createRootRoute,
  createRoute,
  Outlet,
  redirect,
} from '@tanstack/react-router'
import { fetchAuthStatus, getBaseUrl } from '@/lib/api'
import { DashboardPage } from '@/pages/dashboard'
import { ListPage } from '@/pages/list'
import { DetailPage } from '@/pages/detail'
import { CreatePage } from '@/pages/create'
import { EditPage } from '@/pages/edit'
import { LoginPage } from '@/pages/login'

const rootRoute = createRootRoute({
  component: Outlet,
})

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage,
})

const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: DashboardPage,
  beforeLoad: async () => {
    try {
      const status = await fetchAuthStatus()
      if (status.has_auth && !status.authenticated) {
        throw redirect({ to: '/login' })
      }
    } catch (e: any) {
      if (e?.to === '/login' || e?.redirect) throw e
      // If auth check fails, try to proceed (might not have auth)
    }
  },
})

const listRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/$identity/list',
  component: function ListRouteComponent() {
    const { identity } = listRoute.useParams()
    return <ListPage identity={identity} />
  },
  beforeLoad: async () => {
    try {
      const status = await fetchAuthStatus()
      if (status.has_auth && !status.authenticated) {
        throw redirect({ to: '/login' })
      }
    } catch (e: any) {
      if (e?.to === '/login' || e?.redirect) throw e
    }
  },
})

const createRouteConfig = createRoute({
  getParentRoute: () => rootRoute,
  path: '/$identity/create',
  component: function CreateRouteComponent() {
    const { identity } = createRouteConfig.useParams()
    return <CreatePage identity={identity} />
  },
  beforeLoad: async () => {
    try {
      const status = await fetchAuthStatus()
      if (status.has_auth && !status.authenticated) {
        throw redirect({ to: '/login' })
      }
    } catch (e: any) {
      if (e?.to === '/login' || e?.redirect) throw e
    }
  },
})

const detailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/$identity/$pk',
  component: function DetailRouteComponent() {
    const { identity, pk } = detailRoute.useParams()
    return <DetailPage identity={identity} pk={pk} />
  },
  beforeLoad: async () => {
    try {
      const status = await fetchAuthStatus()
      if (status.has_auth && !status.authenticated) {
        throw redirect({ to: '/login' })
      }
    } catch (e: any) {
      if (e?.to === '/login' || e?.redirect) throw e
    }
  },
})

const editRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/$identity/$pk/edit',
  component: function EditRouteComponent() {
    const { identity, pk } = editRoute.useParams()
    return <EditPage identity={identity} pk={pk} />
  },
  beforeLoad: async () => {
    try {
      const status = await fetchAuthStatus()
      if (status.has_auth && !status.authenticated) {
        throw redirect({ to: '/login' })
      }
    } catch (e: any) {
      if (e?.to === '/login' || e?.redirect) throw e
    }
  },
})

const routeTree = rootRoute.addChildren([
  loginRoute,
  dashboardRoute,
  listRoute,
  createRouteConfig,
  editRoute,
  detailRoute,
])

export const router = createRouter({
  routeTree,
  basepath: getBaseUrl(),
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
