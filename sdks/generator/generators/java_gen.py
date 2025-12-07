"""
Java SDK generator.
"""

from pathlib import Path
from typing import List
from .base import BaseSDKGenerator, GenerationResult


class JavaGenerator(BaseSDKGenerator):
    """Java SDK generator"""

    def get_language(self) -> str:
        return "java"

    def generate(self, output_dir: str) -> GenerationResult:
        """Generate Java SDK"""
        self.output_dir = Path(output_dir)
        files_created = []

        # Create Maven structure
        src_main = self.output_dir / "src" / "main" / "java" / "ai" / "continuum"
        src_main.mkdir(parents=True, exist_ok=True)

        files_created.extend(self.generate_models())
        files_created.append(self.generate_client())
        files_created.extend(self.generate_package_files())

        return GenerationResult(
            language=self.get_language(),
            output_dir=self.output_dir,
            files_created=files_created,
            success=True,
        )

    def generate_models(self) -> List[Path]:
        """Generate Java model classes"""
        base_path = self.output_dir / "src" / "main" / "java" / "ai" / "continuum" / "models"
        base_path.mkdir(parents=True, exist_ok=True)

        file_path = base_path / "Memory.java"
        content = '''package ai.continuum.models;

import java.time.OffsetDateTime;
import java.util.Map;

public class Memory {
    private String id;
    private String content;
    private String memoryType;
    private Double importance;
    private Map<String, Object> metadata;
    private OffsetDateTime createdAt;
    private OffsetDateTime updatedAt;

    // Getters and setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public String getMemoryType() { return memoryType; }
    public void setMemoryType(String memoryType) { this.memoryType = memoryType; }

    public Double getImportance() { return importance; }
    public void setImportance(Double importance) { this.importance = importance; }

    public Map<String, Object> getMetadata() { return metadata; }
    public void setMetadata(Map<String, Object> metadata) { this.metadata = metadata; }

    public OffsetDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(OffsetDateTime createdAt) { this.createdAt = createdAt; }

    public OffsetDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(OffsetDateTime updatedAt) { this.updatedAt = updatedAt; }
}
'''
        return [self.write_file(file_path, content)]

    def generate_client(self) -> Path:
        """Generate Java client"""
        base_path = self.output_dir / "src" / "main" / "java" / "ai" / "continuum"
        file_path = base_path / "ContinuumClient.java"

        content = '''package ai.continuum;

import ai.continuum.models.Memory;
import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.*;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

public class ContinuumClient {
    private final String baseUrl;
    private final String apiKey;
    private final OkHttpClient httpClient;
    private final ObjectMapper objectMapper;

    private ContinuumClient(Builder builder) {
        this.baseUrl = builder.baseUrl;
        this.apiKey = builder.apiKey;
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .build();
        this.objectMapper = new ObjectMapper();
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private String baseUrl = "https://api.continuum.ai/v1";
        private String apiKey;

        public Builder baseUrl(String baseUrl) {
            this.baseUrl = baseUrl;
            return this;
        }

        public Builder apiKey(String apiKey) {
            this.apiKey = apiKey;
            return this;
        }

        public ContinuumClient build() {
            return new ContinuumClient(this);
        }
    }

    public MemoriesResource memories() {
        return new MemoriesResource(this);
    }

    public class MemoriesResource {
        private final ContinuumClient client;

        MemoriesResource(ContinuumClient client) {
            this.client = client;
        }

        public Memory create(CreateMemoryInput input) throws IOException {
            // Implementation
            return null;
        }
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
        content = f'''# CONTINUUM Java SDK

Official Java client for CONTINUUM API.

## Installation

Maven:

```xml
<dependency>
    <groupId>ai.continuum</groupId>
    <artifactId>continuum-java</artifactId>
    <version>{self.spec.api_version}</version>
</dependency>
```

Gradle:

```gradle
implementation 'ai.continuum:continuum-java:{self.spec.api_version}'
```

## Usage

```java
import ai.continuum.ContinuumClient;
import ai.continuum.models.*;

ContinuumClient client = ContinuumClient.builder()
    .apiKey("your-api-key")
    .build();

Memory memory = client.memories().create(CreateMemoryInput.builder()
    .content("Important insight")
    .memoryType("semantic")
    .importance(0.9)
    .build());
```

## Version

{self.spec.api_version}
'''
        return [self.write_file(file_path, content, format=False)]

    def generate_package_files(self) -> List[Path]:
        """Generate pom.xml"""
        file_path = self.output_dir / "pom.xml"
        content = f'''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>ai.continuum</groupId>
    <artifactId>continuum-java</artifactId>
    <version>{self.spec.api_version}</version>
    <packaging>jar</packaging>

    <name>CONTINUUM Java SDK</name>
    <description>{self.spec.description}</description>

    <dependencies>
        <dependency>
            <groupId>com.squareup.okhttp3</groupId>
            <artifactId>okhttp</artifactId>
            <version>4.12.0</version>
        </dependency>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.15.0</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
'''
        return [self.write_file(file_path, content, format=False)]
