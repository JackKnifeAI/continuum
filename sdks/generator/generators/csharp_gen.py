"""
C# SDK generator.
"""

from pathlib import Path
from typing import List
from .base import BaseSDKGenerator, GenerationResult


class CSharpGenerator(BaseSDKGenerator):
    """C# SDK generator"""

    def get_language(self) -> str:
        return "csharp"

    def generate(self, output_dir: str) -> GenerationResult:
        """Generate C# SDK"""
        self.output_dir = Path(output_dir)
        files_created = []

        (self.output_dir / "Continuum").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "Continuum" / "Models").mkdir(exist_ok=True)

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
        """Generate C# model classes"""
        file_path = self.output_dir / "Continuum" / "Models" / "Memory.cs"
        content = '''using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Continuum.Models
{
    public class Memory
    {
        [JsonPropertyName("id")]
        public string Id { get; set; }

        [JsonPropertyName("content")]
        public string Content { get; set; }

        [JsonPropertyName("memory_type")]
        public string MemoryType { get; set; }

        [JsonPropertyName("importance")]
        public double Importance { get; set; }

        [JsonPropertyName("metadata")]
        public Dictionary<string, object> Metadata { get; set; }

        [JsonPropertyName("created_at")]
        public DateTimeOffset CreatedAt { get; set; }

        [JsonPropertyName("updated_at")]
        public DateTimeOffset? UpdatedAt { get; set; }
    }

    public class CreateMemoryInput
    {
        [JsonPropertyName("content")]
        public string Content { get; set; }

        [JsonPropertyName("memory_type")]
        public string MemoryType { get; set; }

        [JsonPropertyName("importance")]
        public double? Importance { get; set; }

        [JsonPropertyName("metadata")]
        public Dictionary<string, object> Metadata { get; set; }
    }
}
'''
        return [self.write_file(file_path, content)]

    def generate_client(self) -> Path:
        """Generate C# client"""
        file_path = self.output_dir / "Continuum" / "ContinuumClient.cs"
        content = '''using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using Continuum.Models;

namespace Continuum
{
    public class ContinuumClient : IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly string _baseUrl;

        public ContinuumClient(string apiKey, string baseUrl = "https://api.continuum.ai/v1")
        {
            _baseUrl = baseUrl.TrimEnd('/');
            _httpClient = new HttpClient();
            _httpClient.DefaultRequestHeaders.Add("X-API-Key", apiKey);
        }

        public MemoriesResource Memories => new MemoriesResource(this);

        internal async Task<T> RequestAsync<T>(
            HttpMethod method,
            string path,
            object body = null)
        {
            var request = new HttpRequestMessage(method, $"{_baseUrl}{path}");

            if (body != null)
            {
                request.Content = JsonContent.Create(body);
            }

            var response = await _httpClient.SendAsync(request);
            response.EnsureSuccessStatusCode();

            return await response.Content.ReadFromJsonAsync<T>();
        }

        public void Dispose()
        {
            _httpClient?.Dispose();
        }
    }

    public class MemoriesResource
    {
        private readonly ContinuumClient _client;

        internal MemoriesResource(ContinuumClient client)
        {
            _client = client;
        }

        public async Task<Memory> CreateAsync(CreateMemoryInput input)
        {
            return await _client.RequestAsync<Memory>(
                HttpMethod.Post,
                "/memories",
                input
            );
        }

        public async Task<Memory> GetAsync(string memoryId)
        {
            return await _client.RequestAsync<Memory>(
                HttpMethod.Get,
                $"/memories/{memoryId}"
            );
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
        content = f'''# CONTINUUM C# SDK

Official C# client for CONTINUUM API.

## Installation

```bash
dotnet add package Continuum
```

## Usage

```csharp
using Continuum;
using Continuum.Models;

var client = new ContinuumClient(apiKey: "your-api-key");

var memory = await client.Memories.CreateAsync(new CreateMemoryInput
{{
    Content = "Important insight",
    MemoryType = "semantic",
    Importance = 0.9
}});
```

## Version

{self.spec.api_version}
'''
        return [self.write_file(file_path, content, format=False)]

    def generate_package_files(self) -> List[Path]:
        """Generate .csproj file"""
        file_path = self.output_dir / "Continuum" / "Continuum.csproj"
        content = f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
    <Version>{self.spec.api_version}</Version>
    <Description>{self.spec.description}</Description>
    <PackageId>Continuum</PackageId>
    <Authors>CONTINUUM</Authors>
    <PackageLicenseExpression>MIT</PackageLicenseExpression>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="System.Net.Http.Json" Version="7.0.0" />
  </ItemGroup>
</Project>
'''
        return [self.write_file(file_path, content, format=False)]
