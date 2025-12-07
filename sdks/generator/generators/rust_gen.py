"""
Rust SDK generator.
"""

from pathlib import Path
from typing import List
from .base import BaseSDKGenerator, GenerationResult


class RustGenerator(BaseSDKGenerator):
    """Rust SDK generator"""

    def get_language(self) -> str:
        return "rust"

    def generate(self, output_dir: str) -> GenerationResult:
        """Generate Rust SDK"""
        self.output_dir = Path(output_dir)
        files_created = []

        (self.output_dir / "src").mkdir(parents=True, exist_ok=True)

        files_created.append(self.generate_client())
        files_created.extend(self.generate_models())
        files_created.extend(self.generate_package_files())

        return GenerationResult(
            language=self.get_language(),
            output_dir=self.output_dir,
            files_created=files_created,
            success=True,
        )

    def generate_models(self) -> List[Path]:
        """Generate Rust structs"""
        file_path = self.output_dir / "src" / "models.rs"
        content = '''use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Memory {
    pub id: String,
    pub content: String,
    pub memory_type: String,
    pub importance: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<serde_json::Value>,
    pub created_at: DateTime<Utc>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub updated_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateMemoryInput {
    pub content: String,
    pub memory_type: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub importance: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<serde_json::Value>,
}
'''
        return [self.write_file(file_path, content)]

    def generate_client(self) -> Path:
        """Generate Rust client"""
        file_path = self.output_dir / "src" / "lib.rs"
        content = '''//! CONTINUUM Rust SDK

use reqwest::{Client as HttpClient, Response};
use serde::{Deserialize, Serialize};
use std::time::Duration;

pub mod models;
pub use models::*;

#[derive(Debug, Clone)]
pub struct Client {
    base_url: String,
    api_key: Option<String>,
    http_client: HttpClient,
}

impl Client {
    pub fn new(api_key: impl Into<String>) -> Self {
        Self {
            base_url: "https://api.continuum.ai/v1".to_string(),
            api_key: Some(api_key.into()),
            http_client: HttpClient::builder()
                .timeout(Duration::from_secs(30))
                .build()
                .expect("Failed to create HTTP client"),
        }
    }

    pub fn memories(&self) -> MemoriesResource {
        MemoriesResource { client: self }
    }

    async fn request<T: for<'de> Deserialize<'de>>(
        &self,
        method: reqwest::Method,
        path: &str,
        body: Option<impl Serialize>,
    ) -> Result<T, Box<dyn std::error::Error>> {
        let url = format!("{}{}", self.base_url, path);
        let mut req = self.http_client.request(method, &url);

        if let Some(api_key) = &self.api_key {
            req = req.header("X-API-Key", api_key);
        }

        if let Some(body) = body {
            req = req.json(&body);
        }

        let response = req.send().await?;
        let data = response.json().await?;
        Ok(data)
    }
}

pub struct MemoriesResource<'a> {
    client: &'a Client,
}

impl<'a> MemoriesResource<'a> {
    pub async fn create(&self, input: CreateMemoryInput) -> Result<Memory, Box<dyn std::error::Error>> {
        self.client.request(reqwest::Method::POST, "/memories", Some(input)).await
    }
}
'''
        return self.write_file(file_path, content)

    def generate_resources(self) -> List[Path]:
        return []

    def generate_auth(self) -> Path:
        return Path()

    def generate_errors(self) -> Path:
        return Path()

    def generate_utils(self) -> List[Path]:
        return []

    def generate_tests(self) -> List[Path]:
        return []

    def generate_docs(self) -> List[Path]:
        """Generate README"""
        file_path = self.output_dir / "README.md"
        content = f'''# CONTINUUM Rust SDK

Official Rust client for CONTINUUM API.

## Installation

Add to `Cargo.toml`:

```toml
[dependencies]
continuum = "{self.spec.api_version}"
```

## Usage

```rust
use continuum::{{Client, CreateMemoryInput}};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {{
    let client = Client::new("your-api-key");

    let memory = client.memories().create(CreateMemoryInput {{
        content: "Important insight".to_string(),
        memory_type: "semantic".to_string(),
        importance: Some(0.9),
        metadata: None,
    }}).await?;

    Ok(())
}}
```

## Version

{self.spec.api_version}
'''
        return [self.write_file(file_path, content, format=False)]

    def generate_package_files(self) -> List[Path]:
        """Generate Cargo.toml"""
        file_path = self.output_dir / "Cargo.toml"
        content = f'''[package]
name = "continuum"
version = "{self.spec.api_version}"
edition = "2021"
description = "{self.spec.description}"
license = "MIT"

[dependencies]
reqwest = {{ version = "0.11", features = ["json"] }}
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
tokio = {{ version = "1.0", features = ["full"] }}
chrono = {{ version = "0.4", features = ["serde"] }}
'''
        return [self.write_file(file_path, content, format=False)]
