using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Forms;
using WorkloadAutomateTool.Services;

namespace WorkloadAutomateTool.Forms.Tasks.HADDAD
{
    public partial class PDFToExcelForm : Form
    {
        private readonly HttpClient _http = new HttpClient();
        private readonly List<string> _selectedFiles = new List<string>();
        private string _token = null;

        public PDFToExcelForm()
        {
            InitializeComponent();
            _http.Timeout = TimeSpan.FromMinutes(30);
            LoadConfigToUi();
            SetUiState();
            AppendLine("Ready.");
        }

        private void LoadConfigToUi()
        {
            try
            {
                txtServerUrl.Text = "http://127.0.0.1:8000";
                txtUsername.Text = "";
            }
            catch
            {
                if (string.IsNullOrWhiteSpace(txtServerUrl.Text))
                    txtServerUrl.Text = "http://127.0.0.1:8000";
            }
        }

        private void SaveUserSettings()
        {
        }

        private void SetUiState()
        {
            bool loggedIn = !string.IsNullOrEmpty(_token);
            btnChoosePdfs.Enabled = loggedIn;
            btnUploadRun.Enabled = loggedIn;
            lblStatus.Text = loggedIn ? "Status: Logged in" : "Status: Not logged in";
        }

        private void SetBusy(bool busy, string statusText = null)
        {
            if (InvokeRequired)
            {
                BeginInvoke(new Action(() => SetBusy(busy, statusText)));
                return;
            }

            txtServerUrl.Enabled = !busy;
            txtUsername.Enabled = !busy;
            txtPassword.Enabled = !busy;
            btnLogin.Enabled = !busy;
            btnChoosePdfs.Enabled = !busy && !string.IsNullOrEmpty(_token);
            btnUploadRun.Enabled = !busy && !string.IsNullOrEmpty(_token);
            progressBar1.Visible = busy;

            if (!string.IsNullOrEmpty(statusText))
                lblStatus.Text = statusText;
        }

        private void AppendLine(string s)
        {
            if (txtLog.InvokeRequired)
            {
                txtLog.BeginInvoke(new Action(() => AppendLine(s)));
                return;
            }
            txtLog.AppendText($"[{DateTime.Now:HH:mm:ss}] {s}{Environment.NewLine}");
        }

        private async void BtnLogin_Click(object sender, EventArgs e)
        {
            try
            {
                var server = txtServerUrl.Text.Trim().TrimEnd('/');
                var user = txtUsername.Text.Trim();
                var pass = txtPassword.Text;

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

            using (var content = new StringContent(json, Encoding.UTF8, "application/json"))
            {
                var resp = await _http.PostAsync(url, content);
                var body = await resp.Content.ReadAsStringAsync();

                if (!resp.IsSuccessStatusCode)
                    throw new Exception($"HTTP {(int)resp.StatusCode}: {body}");

                using (var doc = JsonDocument.Parse(body))
                    return doc.RootElement.GetProperty("access_token").GetString();
            }
        }

        private void BtnChoosePdfs_Click(object sender, EventArgs e)
        {
            using (var dlg = new OpenFileDialog())
            {
                dlg.Filter = "PDF files (*.pdf)|*.pdf";
                dlg.Multiselect = true;
                dlg.Title = "Select PDF files to upload";

                if (dlg.ShowDialog() != DialogResult.OK) return;

                _selectedFiles.Clear();
                _selectedFiles.AddRange(dlg.FileNames);

                lstFiles.Items.Clear();
                foreach (var f in _selectedFiles) lstFiles.Items.Add(f);

                AppendLine($"Selected {_selectedFiles.Count} file(s).");
                lblStatus.Text = $"Status: Selected {_selectedFiles.Count} file(s)";
            }
        }

        private async void BtnUploadRun_Click(object sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(_token))
            {
                MessageBox.Show("Please login first.");
                return;
            }

            if (_selectedFiles.Count == 0)
            {
                MessageBox.Show("Please choose PDFs first.");
                return;
            }

            txtLog.Clear();
            AppendLine("Upload started...");

            try
            {
                var server = txtServerUrl.Text.Trim().TrimEnd('/');
                SetBusy(true, "Status: Uploading / Running...");

                var jobId = await CreateJobUploadFiles(server, _selectedFiles);
                AppendLine($"Created job: {jobId}");
                AppendLine("Done");
                SetBusy(false, "Status: Done");
            }
            catch (Exception ex)
            {
                AppendLine("Error: " + ex.Message);
                SetBusy(false, "Status: Error");
                MessageBox.Show("Error: " + ex.Message);
            }
            finally
            {
                SetUiState();
            }
        }

private async Task<string> CreateJobUploadFiles(string server, List<string> files)
        {
            // Get token from AuthService
            var token = AuthService.Instance.Token;
            var encodedToken = Uri.EscapeDataString(token);
            
            var url = $"{server}/api/v1/jobs?task_code=PDF_TO_EXCEL&token={encodedToken}";
            
            using (var form = new MultipartFormDataContent())
            {
                foreach (var path in files)
                {
                    var fileName = Path.GetFileName(path);
                    var bytes = File.ReadAllBytes(path);
                    var part = new ByteArrayContent(bytes);
                    part.Headers.ContentType = MediaTypeHeaderValue.Parse("application/pdf");
                    form.Add(part, "files", fileName);
                }
                
                var resp = await _http.PostAsync(url, form);
                var body = await resp.Content.ReadAsStringAsync();

                if (!resp.IsSuccessStatusCode)
                    throw new Exception($"Upload failed HTTP {(int)resp.StatusCode}: {body}");

                using (var doc = JsonDocument.Parse(body))
                    return doc.RootElement.GetProperty("job_id").GetString();
            }
        }

        private void BtnClearLog_Click(object sender, EventArgs e)
        {
            txtLog.Clear();
        }

        private void BtnCopyLog_Click(object sender, EventArgs e)
        {
            if (!string.IsNullOrEmpty(txtLog.Text))
                Clipboard.SetText(txtLog.Text);
        }

        private void BtnBack_Click(object sender, EventArgs e)
        {
            this.Close();
        }
    }
}