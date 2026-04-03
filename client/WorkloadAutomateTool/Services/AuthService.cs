using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading.Tasks;

namespace WorkloadAutomateTool.Services
{
    public class AuthService
    {
        private static readonly Lazy<AuthService> _instance = new Lazy<AuthService>(() => new AuthService());
        public static AuthService Instance => _instance.Value;

        private readonly HttpClient _http = new HttpClient();
        private string _token = null;
        private string _currentCustomer = null;
        private string _currentMenu = null;
        private string _serverUrl = null;

        public string Token => _token;
        public string CurrentCustomer => _currentCustomer;
        public string CurrentMenu => _currentMenu;
        public string ServerUrl => _serverUrl;
        public bool IsLoggedIn => !string.IsNullOrEmpty(_token);
        public HttpClient Http => _http;

        private AuthService()
        {
            _http.Timeout = TimeSpan.FromMinutes(5);
        }

        public void SetServerUrl(string url)
        {
            _serverUrl = url?.Trim().TrimEnd('/');
        }

        public void SetCurrentMenu(string menuCode)
        {
            _currentMenu = menuCode;
            UpdateRequestHeaders();
        }

        private void UpdateRequestHeaders()
        {
            _http.DefaultRequestHeaders.Remove("X-Customer-Code");
            _http.DefaultRequestHeaders.Remove("X-Menu-Code");

            if (!string.IsNullOrEmpty(_currentCustomer))
            {
                _http.DefaultRequestHeaders.Add("X-Customer-Code", _currentCustomer);
            }
            if (!string.IsNullOrEmpty(_currentMenu))
            {
                _http.DefaultRequestHeaders.Add("X-Menu-Code", _currentMenu);
            }
        }

        public async Task<(bool success, string message)> Login(string customer, string username, string password)
        {
            if (string.IsNullOrEmpty(_serverUrl))
            {
                return (false, "Server URL not configured");
            }

            try
            {
                var url = $"{_serverUrl}/api/v1/auth/login";
                var payload = new { username = username, password = password };
                var json = JsonSerializer.Serialize(payload);

                using (var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json"))
                {
                    var resp = await _http.PostAsync(url, content);
                    var body = await resp.Content.ReadAsStringAsync();

                    if (!resp.IsSuccessStatusCode)
                    {
                        var errorMsg = "Invalid username/password";
                        try
                        {
                            using (var doc = JsonDocument.Parse(body))
                            {
                                if (doc.RootElement.TryGetProperty("detail", out var detail))
                                    errorMsg = detail.GetString();
                            }
                        }
                        catch { }
                        return (false, errorMsg);
                    }

                    using (var doc = JsonDocument.Parse(body))
                    {
                        if (doc.RootElement.TryGetProperty("access_token", out var token))
                        {
                            _token = token.GetString();
                            _currentCustomer = customer;
                            _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", _token);
                            UpdateRequestHeaders();
                            return (true, "Login successful");
                        }
                        return (false, "Invalid response from server");
                    }
                }
            }
            catch (HttpRequestException ex)
            {
                return (false, $"Connection failed: {ex.Message}");
            }
            catch (TaskCanceledException)
            {
                return (false, "Connection timeout");
            }
            catch (Exception ex)
            {
                return (false, $"Error: {ex.Message}");
            }
        }

        public void Logout()
        {
            _token = null;
            _currentCustomer = null;
            _currentMenu = null;
            _http.DefaultRequestHeaders.Authorization = null;
            _http.DefaultRequestHeaders.Remove("X-Customer-Code");
            _http.DefaultRequestHeaders.Remove("X-Menu-Code");
        }

        public void RequireLogin()
        {
            if (!IsLoggedIn)
                throw new InvalidOperationException("Not logged in");
        }
    }
}
