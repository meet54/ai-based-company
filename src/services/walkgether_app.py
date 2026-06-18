"""Walkgether React Native app scaffold and interactive mobile preview."""

from html import escape


def build_walkgether_app_files() -> list[dict]:
    """Write React Native project structure for Walkgether MVP."""
    return [
        {"path": "mobile/package.json", "content": _package_json()},
        {"path": "mobile/App.tsx", "content": _app_tsx()},
        {"path": "mobile/app.json", "content": _app_json()},
        {"path": "mobile/src/navigation/AppNavigator.tsx", "content": _navigator()},
        {"path": "mobile/src/screens/HomeScreen.tsx", "content": _home_screen()},
        {"path": "mobile/src/screens/DiscoverScreen.tsx", "content": _discover_screen()},
        {"path": "mobile/src/screens/MatchesScreen.tsx", "content": _matches_screen()},
        {"path": "mobile/src/screens/ScheduleScreen.tsx", "content": _schedule_screen()},
        {"path": "mobile/src/screens/ChatScreen.tsx", "content": _chat_screen()},
        {"path": "mobile/src/screens/ProfileScreen.tsx", "content": _profile_screen()},
        {"path": "mobile/src/screens/AuthScreen.tsx", "content": _auth_screen()},
        {"path": "mobile/src/theme/colors.ts", "content": _colors()},
        {"path": "mobile/README.md", "content": _mobile_readme()},
        {"path": "mobile-preview/index.html", "content": _mobile_preview_html()},
        {"path": "mobile-preview/styles.css", "content": _mobile_preview_css()},
        {"path": "mobile-preview/app.js", "content": _mobile_preview_js()},
        {"path": "docs/mobile-architecture.md", "content": _mobile_arch_doc()},
    ]


def _package_json() -> str:
    return """{
  "name": "walkgether",
  "version": "0.1.0",
  "main": "expo/AppEntry.js",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios"
  },
  "dependencies": {
    "expo": "~51.0.0",
    "react": "18.2.0",
    "react-native": "0.74.0",
    "@react-navigation/native": "^6.1.0",
    "@react-navigation/bottom-tabs": "^6.5.0",
    "react-native-maps": "1.14.0",
    "expo-location": "~17.0.0",
    "expo-notifications": "~0.28.0"
  }
}
"""


def _app_json() -> str:
    return """{
  "expo": {
    "name": "Walkgether",
    "slug": "walkgether",
    "version": "0.1.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "splash": { "backgroundColor": "#0a0f14" },
    "ios": { "bundleIdentifier": "com.ainexus.walkgether" },
    "android": { "package": "com.ainexus.walkgether" }
  }
}
"""


def _app_tsx() -> str:
    return """import { NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import AppNavigator from './src/navigation/AppNavigator';

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <AppNavigator />
    </NavigationContainer>
  );
}
"""


def _navigator() -> str:
    return """import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import HomeScreen from '../screens/HomeScreen';
import DiscoverScreen from '../screens/DiscoverScreen';
import MatchesScreen from '../screens/MatchesScreen';
import ScheduleScreen from '../screens/ScheduleScreen';
import ChatScreen from '../screens/ChatScreen';
import ProfileScreen from '../screens/ProfileScreen';

const Tab = createBottomTabNavigator();

export default function AppNavigator() {
  return (
    <Tab.Navigator screenOptions={{ headerShown: false, tabBarActiveTintColor: '#2dd4a8' }}>
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Discover" component={DiscoverScreen} />
      <Tab.Screen name="Matches" component={MatchesScreen} />
      <Tab.Screen name="Schedule" component={ScheduleScreen} />
      <Tab.Screen name="Chat" component={ChatScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}
"""


def _screen_template(name: str, title: str, subtitle: str) -> str:
    return f"""import {{ View, Text, StyleSheet }} from 'react-native';
import {{ colors }} from '../theme/colors';

export default function {name}() {{
  return (
    <View style={{styles.container}}>
      <Text style={{styles.title}}>{title}</Text>
      <Text style={{styles.sub}}>{subtitle}</Text>
    </View>
  );
}}

const styles = StyleSheet.create({{
  container: {{ flex: 1, backgroundColor: colors.bg, padding: 24, justifyContent: 'center' }},
  title: {{ fontSize: 28, fontWeight: '800', color: colors.text }},
  sub: {{ fontSize: 16, color: colors.muted, marginTop: 8 }},
}});
"""


def _home_screen() -> str:
    return _screen_template("HomeScreen", "Walkgether", "Your walking community — find partners, join groups, stay active.")


def _discover_screen() -> str:
    return _screen_template("DiscoverScreen", "Discover Nearby", "Map view with walkers and groups near you.")


def _matches_screen() -> str:
    return _screen_template("MatchesScreen", "Your Matches", "Compatible walking partners based on pace and schedule.")


def _schedule_screen() -> str:
    return _screen_template("ScheduleScreen", "Schedule Walks", "One-time and recurring walking events.")


def _chat_screen() -> str:
    return _screen_template("ChatScreen", "Messages", "1:1 and group chats with your walking community.")


def _profile_screen() -> str:
    return _screen_template("ProfileScreen", "Your Profile", "Pace, interests, availability, and safety settings.")


def _auth_screen() -> str:
    return _screen_template("AuthScreen", "Welcome", "Sign up with email, phone, Google, or Apple.")


def _colors() -> str:
    return """export const colors = {
  bg: '#0a0f14',
  surface: '#121a22',
  text: '#f0f4f8',
  muted: '#8b9cb3',
  accent: '#2dd4a8',
  accent2: '#38bdf8',
};
"""


def _mobile_readme() -> str:
    return """# Walkgether Mobile App (React Native + Expo)

Cross-platform iOS & Android app for the Walkgether in-house project.

## MVP Screens
- Auth (email, phone, Google, Apple)
- Home dashboard
- Nearby discovery (maps)
- Walk matching
- Schedule walks
- Messaging
- User profile

## Run locally
```bash
cd mobile
npm install
npx expo start
```

Built by AI Nexus Mobile Engineering — Manan Desai & Daxesh Bhoi.
"""


def _mobile_arch_doc() -> str:
    return """# Walkgether Mobile Architecture

## Stack
- **React Native** + **Expo** (iOS & Android)
- **React Navigation** — tab + stack navigators
- **react-native-maps** + **expo-location** — nearby discovery
- **Firebase** — push notifications & chat
- **NestJS API** — auth, profiles, matching, scheduling

## Folder Structure
```
mobile/
  App.tsx
  src/
    navigation/AppNavigator.tsx
    screens/   — Home, Discover, Matches, Schedule, Chat, Profile, Auth
    theme/colors.ts
```

## Team
- Manan Desai — Lead Mobile Developer
- Daxesh Bhoi — App Developer (maps, notifications)
"""


def _mobile_preview_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Walkgether App Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <div class="preview-wrap">
    <div class="phone">
      <div class="status-bar"><span>9:41</span><span>📶 🔋</span></div>
      <div id="screen" class="screen">
        <div class="screen-inner active" data-screen="home">
          <h1>🚶 Walkgether</h1>
          <p class="sub">Good morning! 3 walkers nearby.</p>
          <div class="card"><strong>Morning Walk Group</strong><span>Starts in 45 min · 0.4 mi</span><button>Join</button></div>
          <div class="card"><strong>Priya K.</strong><span>Moderate pace · Evening</span><button>Match</button></div>
          <div class="stats-row"><div><b>4,280</b><small>steps today</small></div><div><b>2</b><small>matches</small></div></div>
        </div>
        <div class="screen-inner" data-screen="discover">
          <h2>Discover</h2>
          <div class="map-mock">📍 Map · Walkers & groups near you</div>
          <div class="chip-row"><span class="chip active">1 mi</span><span class="chip">Morning</span><span class="chip">Casual</span></div>
          <div class="walker-list">
            <div class="walker"><span>👩</span><div><b>Emma · 0.2 mi</b><small>Dog walks · Daily</small></div><button>Hi</button></div>
            <div class="walker"><span>👨</span><div><b>James · 0.5 mi</b><small>Brisk · Weekends</small></div><button>Hi</button></div>
          </div>
        </div>
        <div class="screen-inner" data-screen="matches">
          <h2>Matches</h2>
          <div class="match-card featured"><div class="match-score">92% match</div><b>Priya Sharma</b><p>Evening walks · Shared interest: parks</p><button>Schedule Walk</button></div>
          <div class="match-card"><b>Tom Lee</b><p>Morning · Moderate pace</p><button>Message</button></div>
        </div>
        <div class="screen-inner" data-screen="schedule">
          <h2>Schedule</h2>
          <div class="event"><span class="date">Today</span><b>Sunset Walk</b><small>6:30 PM · Riverside Trail</small></div>
          <div class="event"><span class="date">Sat</span><b>Weekend Group Walk</b><small>8:00 AM · Central Park</small></div>
          <button class="fab">+ New Walk</button>
        </div>
        <div class="screen-inner" data-screen="chat">
          <h2>Messages</h2>
          <div class="chat-item unread"><b>Priya</b><p>See you at 6:30! 🚶</p><span>2m</span></div>
          <div class="chat-item"><b>Morning Walkers</b><p>Marcus: Great route today</p><span>1h</span></div>
        </div>
        <div class="screen-inner" data-screen="profile">
          <div class="avatar">👤</div>
          <h2>Meet Suthar</h2>
          <p class="sub">Casual pace · Evenings · Parks & trails</p>
          <div class="profile-stats"><div><b>28</b><small>Walks</small></div><div><b>12</b><small>Friends</small></div><div><b>4.9</b><small>Rating</small></div></div>
          <button class="outline-btn">Edit Profile</button>
        </div>
      </div>
      <nav class="tab-bar">
        <button class="tab active" data-tab="home">🏠<span>Home</span></button>
        <button class="tab" data-tab="discover">📍<span>Discover</span></button>
        <button class="tab" data-tab="matches">🤝<span>Matches</span></button>
        <button class="tab" data-tab="schedule">📅<span>Schedule</span></button>
        <button class="tab" data-tab="chat">💬<span>Chat</span></button>
        <button class="tab" data-tab="profile">👤<span>Profile</span></button>
      </nav>
    </div>
    <div class="preview-label">
      <strong>Walkgether App</strong>
      <span>React Native · iOS & Android MVP</span>
    </div>
  </div>
  <script src="app.js"></script>
</body>
</html>"""


def _mobile_preview_css() -> str:
    return """:root {
  --bg: #0a0f14; --surface: #121a22; --text: #f0f4f8; --muted: #8b9cb3;
  --accent: #2dd4a8; --accent2: #38bdf8;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'DM Sans', system-ui, sans-serif; background: #05080c; min-height: 100vh;
  display: flex; align-items: center; justify-content: center; padding: 1rem; color: var(--text); }
.preview-wrap { text-align: center; }
.phone { width: 320px; background: var(--bg); border-radius: 36px; border: 3px solid #1e2936;
  overflow: hidden; box-shadow: 0 40px 80px rgba(0,0,0,0.6); }
.status-bar { display: flex; justify-content: space-between; padding: 0.6rem 1.2rem;
  font-size: 0.75rem; font-weight: 600; }
.screen { height: 520px; overflow: hidden; position: relative; background: var(--surface); }
.screen-inner { display: none; padding: 1rem 1.1rem; height: 100%; overflow-y: auto; text-align: left; }
.screen-inner.active { display: block; }
.screen-inner h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
.screen-inner h2 { font-size: 1.2rem; margin-bottom: 0.75rem; }
.sub { color: var(--muted); font-size: 0.85rem; margin-bottom: 1rem; }
.card { background: var(--bg); border-radius: 12px; padding: 0.85rem; margin-bottom: 0.65rem;
  border: 1px solid rgba(255,255,255,0.06); }
.card strong { display: block; font-size: 0.9rem; }
.card span { font-size: 0.75rem; color: var(--muted); }
.card button, .walker button, .match-card button { margin-top: 0.5rem; background: var(--accent);
  color: #0a0f14; border: none; padding: 0.35rem 0.75rem; border-radius: 8px; font-weight: 700; font-size: 0.75rem; cursor: pointer; }
.stats-row { display: flex; gap: 1rem; margin-top: 1rem; }
.stats-row b { display: block; color: var(--accent); font-size: 1.25rem; }
.stats-row small { font-size: 0.7rem; color: var(--muted); }
.map-mock { background: rgba(56,189,248,0.12); border-radius: 12px; padding: 3rem 1rem; text-align: center;
  color: var(--accent2); font-size: 0.85rem; margin-bottom: 0.75rem; }
.chip-row { display: flex; gap: 0.4rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.chip { font-size: 0.7rem; padding: 0.3rem 0.6rem; border-radius: 999px; background: var(--bg); color: var(--muted); }
.chip.active { background: rgba(45,212,168,0.2); color: var(--accent); }
.walker { display: flex; align-items: center; gap: 0.6rem; background: var(--bg); padding: 0.65rem;
  border-radius: 10px; margin-bottom: 0.5rem; }
.walker span { font-size: 1.4rem; }
.walker b { display: block; font-size: 0.85rem; }
.walker small { font-size: 0.7rem; color: var(--muted); }
.walker button { margin-left: auto; margin-top: 0; }
.match-card { background: var(--bg); border-radius: 12px; padding: 0.85rem; margin-bottom: 0.6rem;
  border: 1px solid rgba(255,255,255,0.06); }
.match-card.featured { border-color: rgba(45,212,168,0.35); }
.match-score { font-size: 0.65rem; color: var(--accent); font-weight: 700; margin-bottom: 0.25rem; }
.match-card p { font-size: 0.75rem; color: var(--muted); margin: 0.25rem 0 0.5rem; }
.event { background: var(--bg); padding: 0.75rem; border-radius: 10px; margin-bottom: 0.5rem; }
.event .date { font-size: 0.65rem; color: var(--accent2); font-weight: 700; display: block; }
.event b { font-size: 0.9rem; }
.event small { font-size: 0.72rem; color: var(--muted); display: block; }
.fab { width: 100%; margin-top: 0.75rem; padding: 0.65rem; background: var(--accent); color: #0a0f14;
  border: none; border-radius: 10px; font-weight: 700; cursor: pointer; }
.chat-item { display: flex; flex-wrap: wrap; gap: 0.25rem; padding: 0.65rem 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
.chat-item b { flex: 1; font-size: 0.85rem; }
.chat-item p { width: 100%; font-size: 0.75rem; color: var(--muted); margin: 0; }
.chat-item span { font-size: 0.65rem; color: var(--muted); }
.chat-item.unread b { color: var(--accent); }
.avatar { font-size: 3rem; text-align: center; margin: 0.5rem 0; }
.profile-stats { display: flex; justify-content: space-around; margin: 1rem 0; }
.profile-stats b { display: block; color: var(--accent); font-size: 1.2rem; }
.profile-stats small { font-size: 0.65rem; color: var(--muted); }
.outline-btn { width: 100%; padding: 0.6rem; background: transparent; border: 1px solid rgba(255,255,255,0.15);
  color: var(--text); border-radius: 10px; cursor: pointer; }
.tab-bar { display: flex; background: var(--bg); border-top: 1px solid rgba(255,255,255,0.06); padding: 0.35rem 0; }
.tab { flex: 1; background: none; border: none; color: var(--muted); font-size: 0.55rem; cursor: pointer;
  display: flex; flex-direction: column; align-items: center; gap: 0.15rem; padding: 0.35rem 0; }
.tab span { font-size: 0.55rem; }
.tab.active { color: var(--accent); }
.preview-label { margin-top: 1.25rem; }
.preview-label strong { display: block; font-size: 1rem; }
.preview-label span { font-size: 0.8rem; color: var(--muted); }
"""


def _mobile_preview_js() -> str:
    return """document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const id = tab.dataset.tab;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.screen-inner').forEach(s => s.classList.remove('active'));
    tab.classList.add('active');
    document.querySelector(`[data-screen="${id}"]`)?.classList.add('active');
  });
});
"""
