import MapPage from "@/pages/MapPage.vue";
import AboutPage from "@/pages/AboutPage.vue"
import type {RouteRecordRaw} from "vue-router";

/**
 * Sets router url endpoints to specific pages
 */
const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "Map",
    component: MapPage
  },
  {
    path: "/about",
    name: "About",
    component: AboutPage
  },
  {
    path: '*',
    redirect: '/'
  }
];
export default routes;
