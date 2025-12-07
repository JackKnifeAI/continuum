/**
 * CONTINUUM iOS Native Module
 * Provides native functionality for embeddings, secure storage, and background sync
 */

import Foundation
import CoreML

@objc(ContinuumModule)
class ContinuumModule: NSObject {

  // MARK: - Embedding Generation

  @objc
  func generateEmbedding(_ text: String,
                        resolver: @escaping RCTPromiseResolveBlock,
                        rejecter: @escaping RCTPromiseRejectBlock) {

    let startTime = CFAbsoluteTimeGetCurrent()

    // TODO: Load CoreML embedding model
    // For now, return mock embedding
    let dimensions = 384
    let embedding = (0..<dimensions).map { _ in Float.random(in: -1...1) }

    let processingTime = CFAbsoluteTimeGetCurrent() - startTime

    let result: [String: Any] = [
      "embedding": embedding,
      "dimensions": dimensions,
      "processingTime": processingTime * 1000 // Convert to ms
    ]

    resolver(result)
  }

  // MARK: - Secure Storage

  @objc
  func secureSet(_ key: String,
                value: String,
                resolver: @escaping RCTPromiseResolveBlock,
                rejecter: @escaping RCTPromiseRejectBlock) {

    let data = value.data(using: .utf8)!

    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrAccount as String: key,
      kSecValueData as String: data,
      kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock
    ]

    // Delete any existing item
    SecItemDelete(query as CFDictionary)

    // Add new item
    let status = SecItemAdd(query as CFDictionary, nil)

    if status == errSecSuccess {
      resolver(nil)
    } else {
      rejecter("KEYCHAIN_ERROR", "Failed to save to keychain: \(status)", nil)
    }
  }

  @objc
  func secureGet(_ key: String,
                resolver: @escaping RCTPromiseResolveBlock,
                rejecter: @escaping RCTPromiseRejectBlock) {

    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrAccount as String: key,
      kSecReturnData as String: true,
      kSecMatchLimit as String: kSecMatchLimitOne
    ]

    var result: AnyObject?
    let status = SecItemCopyMatching(query as CFDictionary, &result)

    if status == errSecSuccess {
      if let data = result as? Data,
         let value = String(data: data, encoding: .utf8) {
        resolver(value)
      } else {
        resolver(nil)
      }
    } else if status == errSecItemNotFound {
      resolver(nil)
    } else {
      rejecter("KEYCHAIN_ERROR", "Failed to read from keychain: \(status)", nil)
    }
  }

  @objc
  func secureRemove(_ key: String,
                   resolver: @escaping RCTPromiseResolveBlock,
                   rejecter: @escaping RCTPromiseRejectBlock) {

    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrAccount as String: key
    ]

    let status = SecItemDelete(query as CFDictionary)

    if status == errSecSuccess || status == errSecItemNotFound {
      resolver(nil)
    } else {
      rejecter("KEYCHAIN_ERROR", "Failed to delete from keychain: \(status)", nil)
    }
  }

  @objc
  func secureClear(_ resolver: @escaping RCTPromiseResolveBlock,
                  rejecter: @escaping RCTPromiseRejectBlock) {

    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword
    ]

    SecItemDelete(query as CFDictionary)
    resolver(nil)
  }

  // MARK: - Background Sync

  @objc
  func configureBackgroundSync(_ options: [String: Any],
                              resolver: @escaping RCTPromiseResolveBlock,
                              rejecter: @escaping RCTPromiseRejectBlock) {

    // Background sync is handled by react-native-background-fetch
    resolver(nil)
  }

  @objc
  static func requiresMainQueueSetup() -> Bool {
    return true
  }
}
