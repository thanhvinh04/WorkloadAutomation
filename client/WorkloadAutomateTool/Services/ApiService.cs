using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using System.Configuration;

namespace WorkloadAutomateTool.Services
{
    public class ApiService
    {
        private static readonly HttpClient httpClient = new HttpClient();
        private static string apiBaseUrl = ConfigurationManager.AppSettings["ApiBaseUrl"] ?? "http://localhost:5000/api/";

        public static async Task<ApiResult> UploadFilesAsync(string[] filePaths, string customerCode)
        {
            try
            {
                using (var content = new MultipartFormDataContent())
                {
                    foreach (var filePath in filePaths)
                    {
                        if (File.Exists(filePath))
                        {
                            var fileContent = new ByteArrayContent(File.ReadAllBytes(filePath));
                            fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/octet-stream");
                            content.Add(fileContent, "files", Path.GetFileName(filePath));
                        }
                    }

                    content.Add(new StringContent(customerCode), "customerCode");

                    var response = await httpClient.PostAsync(apiBaseUrl + "upload", content);
                    var responseContent = await response.Content.ReadAsStringAsync();

                    if (response.IsSuccessStatusCode)
                    {
                        return new ApiResult
                        {
                            Success = true,
                            JobId = responseContent
                        };
                    }
                    else
                    {
                        return new ApiResult
                        {
                            Success = false,
                            ErrorMessage = responseContent
                        };
                    }
                }
            }
            catch (Exception ex)
            {
                return new ApiResult
                {
                    Success = false,
                    ErrorMessage = ex.Message
                };
            }
        }

        public static async Task<ApiResult> PollJobResultAsync(string jobId)
        {
            try
            {
                int maxRetries = 30;
                int retryDelayMs = 2000;

                for (int i = 0; i < maxRetries; i++)
                {
                    var response = await httpClient.GetAsync(apiBaseUrl + $"result/{jobId}");
                    
                    if (response.IsSuccessStatusCode)
                    {
                        var responseContent = await response.Content.ReadAsStringAsync();
                        
                        if (responseContent.Contains("completed") || responseContent.Contains("result"))
                        {
                            return new ApiResult
                            {
                                Success = true,
                                HasResult = true,
                                ResultFilePath = responseContent
                            };
                        }
                    }
                    else if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
                    {
                        return new ApiResult
                        {
                            Success = false,
                            ErrorMessage = "Job not found"
                        };
                    }

                    await Task.Delay(retryDelayMs);
                }

                return new ApiResult
                {
                    Success = false,
                    ErrorMessage = "Timeout waiting for result"
                };
            }
            catch (Exception ex)
            {
                return new ApiResult
                {
                    Success = false,
                    ErrorMessage = ex.Message
                };
            }
        }
    }

    public class ApiResult
    {
        public bool Success { get; set; }
        public string JobId { get; set; }
        public string ErrorMessage { get; set; }
        public bool HasResult { get; set; }
        public string ResultFilePath { get; set; }
    }
}