import { createRouter, createWebHashHistory } from 'vue-router';
import Manage from './components/Manage.vue';
import List from './components/List.vue';
import Player from './components/Player.vue';

const routes = [
  { path: '/manage', component: Manage },
  { path: '/list', component: List },
  { path: '/player', component: Player },
  { path: '/:pathMatch(.*)*', redirect: '/list' }
];

const router = createRouter({
  history: createWebHashHistory(),
  routes
});

export default router;
