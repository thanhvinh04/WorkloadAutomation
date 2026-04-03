using System;
using System.Windows.Forms;
using WorkloadAutomateTool.Services;

namespace WorkloadAutomateTool.Forms
{
    public partial class CustomerMenu : Form
    {
        private readonly string customerCode;
        public CustomerMenu(string customerCode)
        {
            InitializeComponent();
            this.customerCode = customerCode;
        }

        private void CustomerMenu_Load(object sender, EventArgs e)
        {
            if (!ShowLoginIfNeeded())
            {
                this.Close();
                return;
            }

            lblCustomer.Text = customerCode;
            lblTitle.Text = $"{customerCode} - Task Menu";
            LoadTasks();
        }

        private bool ShowLoginIfNeeded()
        {
            var auth = AuthService.Instance;
            if (auth.IsLoggedIn && auth.CurrentCustomer == customerCode)
            {
                return true;
            }

            auth.Logout();
            var loginForm = new LoginForm(customerCode);
            if (loginForm.ShowDialog() != DialogResult.OK)
            {
                return false;
            }

            AuthService.Instance.SetServerUrl(loginForm.ServerUrl);
            return true;
        }

        private void LoadTasks()
        {
            flowLayoutPanelTasks.Controls.Clear();
            var tasks = GetTasksForCustomer(customerCode);
            foreach (var task in tasks)
            {
                var btn = new Button
                {
                    Text = task.Name,
                    Width = 250,
                    Height = 80,
                    Tag = task,
                    Font = new System.Drawing.Font("Segoe UI", 12F, System.Drawing.FontStyle.Bold),
                    BackColor = System.Drawing.Color.FromArgb(0, 120, 215),
                    ForeColor = System.Drawing.Color.White,
                    FlatStyle = FlatStyle.Flat,
                    FlatAppearance = { BorderSize = 0 }
                };
                btn.Click += TaskButton_Click;
                flowLayoutPanelTasks.Controls.Add(btn);
            }
        }

        private System.Collections.Generic.List<TaskInfo> GetTasksForCustomer(string customer)
        {
            switch (customer)
            {
                case "HADDAD":
                    return new System.Collections.Generic.List<TaskInfo>
                    {
                        new TaskInfo { Code = "PHOTO8", Name = "Photo 8 Upload" },
                        new TaskInfo { Code = "PDF_TO_EXCEL", Name = "PDF to Excel" },
                        new TaskInfo { Code = "COSTING", Name = "Costing Sheet" },
                        new TaskInfo { Code = "DELEGATE", Name = "Delegate Function" }
                    };
                case "LTD":
                    return new System.Collections.Generic.List<TaskInfo>
                    {
                        new TaskInfo { Code = "PHOTO8", Name = "Photo 8 Upload" },
                        new TaskInfo { Code = "PDF_TO_EXCEL", Name = "PDF to Excel" }
                    };
                case "GARAN":
                    return new System.Collections.Generic.List<TaskInfo>
                    {
                        new TaskInfo { Code = "PHOTO8", Name = "Photo 8 Upload" },
                        new TaskInfo { Code = "PDF_TO_EXCEL", Name = "PDF to Excel" }
                    };
                default:
                    return new System.Collections.Generic.List<TaskInfo>();
            }
        }

        private void TaskButton_Click(object sender, EventArgs e)
        {
            var btn = sender as Button;
            var task = btn.Tag as TaskInfo;
            OpenTaskForm(task.Code);
        }

        private void OpenTaskForm(string taskCode)
        {
            AuthService.Instance.SetCurrentMenu(taskCode);

            Form taskForm = null;
            switch (taskCode)
            {
                case "PHOTO8":
                    taskForm = new Tasks.HADDAD.Photo8Form();
                    break;
                case "PDF_TO_EXCEL":
                    taskForm = new Tasks.HADDAD.PDFToExcelForm();
                    break;
                case "COSTING":
                    taskForm = new Tasks.HADDAD.CostingForm();
                    break;
                case "DELEGATE":
                    taskForm = new Tasks.HADDAD.DelegateForm();
                    break;
            }
            if (taskForm != null)
            {
                this.Hide();
                taskForm.ShowDialog();
                this.Show();
            }
        }

        private void BtnBack_Click(object sender, EventArgs e)
        {
            this.Close();
        }

        private class TaskInfo
        {
            public string Code { get; set; }
            public string Name { get; set; }
        }
    }
}