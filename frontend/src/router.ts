import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import IncidentsList from './pages/IncidentsList.vue'
import IncidentDetail from './pages/IncidentDetail.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/incidents'
  },
  {
    path: '/incidents',
    name: 'incidents-list',
    component: IncidentsList
  },
  {
    path: '/incidents/:id',
    name: 'incident-detail',
    component: IncidentDetail,
    props: (route) => ({ id: Number(route.params.id) })
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
