/**
 * CONTINUUM React Native SDK - Example App
 */

import React, { useState } from 'react';
import {
  SafeAreaView,
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import {
  ContinuumClient,
  ContinuumProvider,
  MemoryList,
  SearchBar,
  CreateMemoryForm,
  OfflineBanner,
  SyncStatusBadge,
  ConnectionIndicator,
  useSession,
  useMemories,
  useSearch,
} from '@continuum/react-native';

// Initialize client
const client = new ContinuumClient({
  apiUrl: 'https://api.continuum.ai',
  apiKey: process.env.CONTINUUM_API_KEY || '',
  enableOffline: true,
  enableBackgroundSync: true,
  logLevel: 'debug',
});

function AuthScreen() {
  const { session, signIn, signOut } = useSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  if (session) {
    return (
      <View style={styles.authContainer}>
        <Text style={styles.welcomeText}>
          Welcome, {session.user.email}!
        </Text>
        <TouchableOpacity style={styles.button} onPress={signOut}>
          <Text style={styles.buttonText}>Sign Out</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.authContainer}>
      <Text style={styles.title}>Sign In to CONTINUUM</Text>
      <TouchableOpacity
        style={styles.button}
        onPress={() => signIn({ email, password })}
      >
        <Text style={styles.buttonText}>Sign In</Text>
      </TouchableOpacity>
    </View>
  );
}

function MemoriesTab() {
  const [selectedType, setSelectedType] = useState<'episodic' | 'semantic'>(
    'episodic'
  );

  return (
    <View style={styles.tabContainer}>
      <View style={styles.typeSelector}>
        <TouchableOpacity
          style={[
            styles.typeButton,
            selectedType === 'episodic' && styles.typeButtonActive,
          ]}
          onPress={() => setSelectedType('episodic')}
        >
          <Text
            style={[
              styles.typeButtonText,
              selectedType === 'episodic' && styles.typeButtonTextActive,
            ]}
          >
            Episodic
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.typeButton,
            selectedType === 'semantic' && styles.typeButtonActive,
          ]}
          onPress={() => setSelectedType('semantic')}
        >
          <Text
            style={[
              styles.typeButtonText,
              selectedType === 'semantic' && styles.typeButtonTextActive,
            ]}
          >
            Semantic
          </Text>
        </TouchableOpacity>
      </View>

      <MemoryList
        filter={{ type: selectedType }}
        onMemoryPress={(memory) => console.log('Memory pressed:', memory)}
      />
    </View>
  );
}

function SearchTab() {
  const { results, search, isLoading } = useSearch();

  return (
    <View style={styles.tabContainer}>
      <SearchBar onSearch={search} placeholder="Search memories..." />

      {isLoading && <Text style={styles.loadingText}>Searching...</Text>}

      <ScrollView>
        {results.map((result) => (
          <View key={result.memory.id} style={styles.searchResult}>
            <Text style={styles.memoryContent}>{result.memory.content}</Text>
            <Text style={styles.similarity}>
              {Math.round(result.similarity * 100)}% match
            </Text>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

function CreateTab() {
  return (
    <View style={styles.tabContainer}>
      <CreateMemoryForm
        onSubmit={(memory) => {
          console.log('Memory created:', memory);
        }}
      />
    </View>
  );
}

function MainApp() {
  const [activeTab, setActiveTab] = useState<'memories' | 'search' | 'create'>(
    'memories'
  );

  return (
    <SafeAreaView style={styles.container}>
      <OfflineBanner />

      <View style={styles.header}>
        <Text style={styles.headerTitle}>CONTINUUM</Text>
        <View style={styles.headerRight}>
          <SyncStatusBadge />
          <ConnectionIndicator />
        </View>
      </View>

      <View style={styles.content}>
        {activeTab === 'memories' && <MemoriesTab />}
        {activeTab === 'search' && <SearchTab />}
        {activeTab === 'create' && <CreateTab />}
      </View>

      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'memories' && styles.tabActive]}
          onPress={() => setActiveTab('memories')}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === 'memories' && styles.tabTextActive,
            ]}
          >
            Memories
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, activeTab === 'search' && styles.tabActive]}
          onPress={() => setActiveTab('search')}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === 'search' && styles.tabTextActive,
            ]}
          >
            Search
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, activeTab === 'create' && styles.tabActive]}
          onPress={() => setActiveTab('create')}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === 'create' && styles.tabTextActive,
            ]}
          >
            Create
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <ContinuumProvider client={client}>
      <MainApp />
    </ContinuumProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  content: {
    flex: 1,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
  },
  tabActive: {
    borderTopWidth: 2,
    borderTopColor: '#3B82F6',
  },
  tabText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#3B82F6',
  },
  tabContainer: {
    flex: 1,
  },
  typeSelector: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  typeButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    alignItems: 'center',
  },
  typeButtonActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  typeButtonText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  typeButtonTextActive: {
    color: '#FFFFFF',
  },
  loadingText: {
    textAlign: 'center',
    padding: 16,
    color: '#6B7280',
  },
  searchResult: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    marginBottom: 8,
    borderRadius: 8,
  },
  memoryContent: {
    fontSize: 15,
    color: '#1F2937',
    marginBottom: 8,
  },
  similarity: {
    fontSize: 12,
    color: '#10B981',
    fontWeight: '600',
  },
  authContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 24,
  },
  welcomeText: {
    fontSize: 18,
    color: '#1F2937',
    marginBottom: 24,
  },
  button: {
    backgroundColor: '#3B82F6',
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderRadius: 8,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
