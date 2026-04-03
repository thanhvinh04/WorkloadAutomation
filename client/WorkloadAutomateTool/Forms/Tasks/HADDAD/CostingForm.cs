using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace WorkloadAutomateTool.Forms.Tasks.HADDAD
{
    public partial class CostingForm : Form
    {
        private readonly HttpClient _http = new HttpClient();
        private string _token = null;

        public CostingForm()
        {
            InitializeComponent();
            _http.Timeout = TimeSpan.FromMinutes(10);
            LoadConfigToUi();
            SetUiState();
            AppendLine("Ready.");
        }

        private string GetServerUrl()
        {
            return cs_txtServerUrl.Text.Trim().TrimEnd('/');
        }

        private async void cs_btnLogin_Click(object sender, EventArgs e)
        {
            try
            {
                var server = GetServerUrl();
                var user = cs_txtUsername.Text.Trim();
                var pass = cs_txtPassword.Text;

                if (string.IsNullOrEmpty(server) || string.IsNullOrEmpty(user) || string.IsNullOrEmpty(pass))
                {
                    MessageBox.Show("Please enter server url, username, password.");
                    return;
                }

                SaveUserSettings();
                SetBusy(true, "Status: Logging in...");
                AppendLine("Login started...");

                _token = await Login(server, user, pass);
                _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", _token);

                AppendLine("Login success.");
                SetBusy(false, "Status: Logged in");
                SetUiState();
            }
            catch (Exception ex)
            {
                _token = null;
                AppendLine("Login failed: " + ex.Message);
                SetBusy(false, "Status: Not logged in");
                SetUiState();
                MessageBox.Show("Login failed: " + ex.Message);
            }
        }

        private async Task<string> Login(string server, string username, string password)
        {
            var url = $"{server}/api/v1/auth/login";
            var payload = new { username = username, password = password };
            var json = JsonSerializer.Serialize(payload);

            using (var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json"))
            {
                var resp = await _http.PostAsync(url, content);
                var body = await resp.Content.ReadAsStringAsync();

                if (!resp.IsSuccessStatusCode)
                    throw new Exception($"HTTP {(int)resp.StatusCode}: {body}");

                using (var doc = JsonDocument.Parse(body))
                    return doc.RootElement.GetProperty("access_token").GetString();
            }
        }

        private void LoadConfigToUi()
        {
            try
            {
                cs_txtServerUrl.Text = "http://127.0.0.1:8000";
                cs_txtUsername.Text = "";
            }
            catch
            {
                if (string.IsNullOrWhiteSpace(cs_txtServerUrl.Text))
                    cs_txtServerUrl.Text = "http://127.0.0.1:8000";
            }
        }

        private void SaveUserSettings()
        {
        }

        private void SetUiState()
        {
            bool loggedIn = !string.IsNullOrEmpty(_token);
            cs_btnLoadData.Enabled = loggedIn;
            cs_btnExportExcel.Enabled = loggedIn;

            if (!loggedIn)
                cs_lblStatus.Text = "Status: Not logged in";
        }

        private void SetBusy(bool busy, string statusText = null)
        {
            if (InvokeRequired)
            {
                BeginInvoke(new Action(() => SetBusy(busy, statusText)));
                return;
            }

            cs_txtServerUrl.Enabled = !busy;
            cs_txtUsername.Enabled = !busy;
            cs_txtPassword.Enabled = !busy;
            cs_btnLogin.Enabled = !busy;

            cs_btnLoadData.Enabled = !busy && !string.IsNullOrEmpty(_token);
            cs_btnExportExcel.Enabled = !busy && !string.IsNullOrEmpty(_token);

            if (!string.IsNullOrEmpty(statusText))
                cs_lblStatus.Text = statusText;
        }

        private void AppendLine(string s)
        {
            if (cs_txtLog.InvokeRequired)
            {
                cs_txtLog.BeginInvoke(new Action(() => AppendLine(s)));
                return;
            }

            cs_txtLog.AppendText($"[{DateTime.Now:HH:mm:ss}] {s}{Environment.NewLine}");
        }

        private async void cs_btnLoadData_Click(object sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(_token))
            {
                MessageBox.Show("Please login first from PDFToSheet screen.");
                return;
            }

            var brand = cs_cboBrand.SelectedItem?.ToString() ?? "HADDAD";

            try
            {
                SetBusy(true, "Status: Loading data...");
                cs_dgvData.DataSource = null;
                cs_txtLog.Clear();
                AppendLine($"Loading costing data for brand: {brand}...");

                var data = await LoadCostingData(brand);

                if (data == null || data.Count == 0)
                {
                    AppendLine("No data found.");
                    SetBusy(false, "Status: No data");
                    return;
                }

                var dt = ConvertToDataTable(data);
                cs_dgvData.DataSource = dt;

                AppendLine($"Loaded {data.Count} row(s).");
                SetBusy(false, $"Status: Loaded {data.Count} row(s)");
            }
            catch (Exception ex)
            {
                AppendLine("Error: " + ex.Message);
                SetBusy(false, "Status: Error");
                MessageBox.Show("Error: " + ex.Message);
            }
        }

        private async Task<List<Dictionary<string, object>>> LoadCostingData(string brand)
        {
            var url = $"{GetServerUrl()}/api/v1/costing/list";
            var payload = new { brand = brand };
            var json = JsonSerializer.Serialize(payload);

            using (var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json"))
            {
                var resp = await _http.PostAsync(url, content);
                var body = await resp.Content.ReadAsStringAsync();

                if (!resp.IsSuccessStatusCode)
                    throw new Exception($"HTTP {(int)resp.StatusCode}: {body}");

                using (var doc = JsonDocument.Parse(body))
                {
                    var result = doc.RootElement;
                    if (result.TryGetProperty("data", out var dataElement))
                    {
                        return JsonSerializer.Deserialize<List<Dictionary<string, object>>>(dataElement.GetRawText());
                    }
                    return new List<Dictionary<string, object>>();
                }
            }
        }

        private async void cs_btnExportExcel_Click(object sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(_token))
            {
                MessageBox.Show("Please login first from PDFToSheet screen.");
                return;
            }

            var brand = cs_cboBrand.SelectedItem?.ToString() ?? "HADDAD";

            using (var dlg = new SaveFileDialog())
            {
                dlg.Filter = "Excel files (*.xlsx)|*.xlsx";
                dlg.FileName = $"Costing_{brand}_{DateTime.Now:yyyyMMdd_HHmmss}.xlsx";

                if (dlg.ShowDialog() != DialogResult.OK) return;

                try
                {
                    SetBusy(true, "Status: Exporting Excel...");
                    AppendLine($"Exporting Excel for brand: {brand}...");

                    await ExportCostingExcel(brand, dlg.FileName);

                    AppendLine($"Exported to: {dlg.FileName}");
                    SetBusy(false, "Status: Export complete");
                    MessageBox.Show("Export complete: " + dlg.FileName);
                }
                catch (Exception ex)
                {
                    AppendLine("Error: " + ex.Message);
                    SetBusy(false, "Status: Error");
                    MessageBox.Show("Error: " + ex.Message);
                }
            }
        }

        private async Task ExportCostingExcel(string brand, string savePath)
        {
            var url = $"{GetServerUrl()}/api/v1/costing/export";
            var payload = new { brand = brand };
            var json = JsonSerializer.Serialize(payload);

            using (var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json"))
            {
                var resp = await _http.PostAsync(url, content);

                if (!resp.IsSuccessStatusCode)
                {
                    var body = await resp.Content.ReadAsStringAsync();
                    throw new Exception($"HTTP {(int)resp.StatusCode}: {body}");
                }

                var bytes = await resp.Content.ReadAsByteArrayAsync();
                File.WriteAllBytes(savePath, bytes);
            }
        }

        private System.Data.DataTable ConvertToDataTable(List<Dictionary<string, object>> data)
        {
            var dt = new System.Data.DataTable();

            if (data == null || data.Count == 0)
                return dt;

            var firstRow = data[0];
            foreach (var key in firstRow.Keys)
            {
                dt.Columns.Add(key, typeof(object));
            }

            foreach (var row in data)
            {
                var dr = dt.NewRow();
                foreach (var kvp in row)
                {
                    dr[kvp.Key] = kvp.Value ?? DBNull.Value;
                }
                dt.Rows.Add(dr);
            }

            return dt;
        }

        private void cs_btnClearLog_Click(object sender, EventArgs e)
        {
            cs_txtLog.Clear();
        }

        private void cs_btnCopyLog_Click(object sender, EventArgs e)
        {
            if (!string.IsNullOrEmpty(cs_txtLog.Text))
                Clipboard.SetText(cs_txtLog.Text);
        }

        private void btnBack_Click(object sender, EventArgs e)
        {
            this.Close();
        }
    }
}
