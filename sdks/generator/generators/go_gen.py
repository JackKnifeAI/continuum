"""
Go SDK generator.
"""

from pathlib import Path
from typing import List
from .base import BaseSDKGenerator, GenerationResult


class GoGenerator(BaseSDKGenerator):
    """Go SDK generator"""

    def get_language(self) -> str:
        return "go"

    def generate(self, output_dir: str) -> GenerationResult:
        """Generate Go SDK"""
        self.output_dir = Path(output_dir)
        files_created = []

        # Create basic structure
        (self.output_dir).mkdir(parents=True, exist_ok=True)

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
        """Generate Go structs"""
        file_path = self.output_dir / "models.go"
        content = '''package continuum

import (
    "time"
)

// Memory represents a memory in CONTINUUM
type Memory struct {
    ID          string                 `json:"id"`
    Content     string                 `json:"content"`
    MemoryType  string                 `json:"memory_type"`
    Importance  float64                `json:"importance"`
    Metadata    map[string]interface{} `json:"metadata,omitempty"`
    CreatedAt   time.Time              `json:"created_at"`
    UpdatedAt   time.Time              `json:"updated_at,omitempty"`
}

// CreateMemoryInput is the input for creating a memory
type CreateMemoryInput struct {
    Content    string                 `json:"content"`
    MemoryType string                 `json:"memory_type"`
    Importance float64                `json:"importance,omitempty"`
    Metadata   map[string]interface{} `json:"metadata,omitempty"`
}
'''
        return [self.write_file(file_path, content)]

    def generate_client(self) -> Path:
        """Generate Go client"""
        file_path = self.output_dir / "client.go"
        content = '''package continuum

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "time"
)

// Client is the CONTINUUM API client
type Client struct {
    baseURL    string
    apiKey     string
    httpClient *http.Client
}

// NewClient creates a new CONTINUUM client
func NewClient(opts ...Option) *Client {
    c := &Client{
        baseURL: "https://api.continuum.ai/v1",
        httpClient: &http.Client{
            Timeout: 30 * time.Second,
        },
    }

    for _, opt := range opts {
        opt(c)
    }

    return c
}

// Option is a client option
type Option func(*Client)

// WithAPIKey sets the API key
func WithAPIKey(apiKey string) Option {
    return func(c *Client) {
        c.apiKey = apiKey
    }
}

// WithBaseURL sets the base URL
func WithBaseURL(baseURL string) Option {
    return func(c *Client) {
        c.baseURL = baseURL
    }
}

// Memories returns the memories resource
func (c *Client) Memories() *MemoriesResource {
    return &MemoriesResource{client: c}
}

// MemoriesResource handles memory operations
type MemoriesResource struct {
    client *Client
}

// Create creates a new memory
func (r *MemoriesResource) Create(input *CreateMemoryInput) (*Memory, error) {
    var result Memory
    err := r.client.request("POST", "/memories", input, &result)
    return &result, err
}

func (c *Client) request(method, path string, body, result interface{}) error {
    var reqBody io.Reader
    if body != nil {
        data, err := json.Marshal(body)
        if err != nil {
            return err
        }
        reqBody = bytes.NewBuffer(data)
    }

    req, err := http.NewRequest(method, c.baseURL+path, reqBody)
    if err != nil {
        return err
    }

    req.Header.Set("Content-Type", "application/json")
    if c.apiKey != "" {
        req.Header.Set("X-API-Key", c.apiKey)
    }

    resp, err := c.httpClient.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    if resp.StatusCode >= 400 {
        return fmt.Errorf("API error: %d", resp.StatusCode)
    }

    if result != nil {
        return json.NewDecoder(resp.Body).Decode(result)
    }

    return nil
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
        content = f'''# CONTINUUM Go SDK

Official Go client for CONTINUUM API.

## Installation

```bash
go get github.com/JackKnifeAI/continuum-go
```

## Usage

```go
package main

import (
    "context"
    "github.com/JackKnifeAI/continuum-go"
)

func main() {{
    client := continuum.NewClient(
        continuum.WithAPIKey("your-api-key"),
    )

    memory, err := client.Memories().Create(&continuum.CreateMemoryInput{{
        Content:    "Important insight",
        MemoryType: "semantic",
        Importance: 0.9,
    }})
}}
```

## Version

{self.spec.api_version}
'''
        return [self.write_file(file_path, content, format=False)]

    def generate_package_files(self) -> List[Path]:
        """Generate go.mod"""
        file_path = self.output_dir / "go.mod"
        content = f'''module github.com/JackKnifeAI/continuum-go

go 1.21

require (
    // dependencies
)
'''
        return [self.write_file(file_path, content, format=False)]
