using System;
using System.Windows.Forms;
using WorkloadAutomateTool.Forms;

namespace WorkloadAutomateTool.Forms
{
    public partial class MainMenu : Form
    {
        public MainMenu()
        {
            InitializeComponent();
        }

        private void MainMenu_Load(object sender, EventArgs e)
        {
            lblTitle.Text = "Workload Automate Tool";
            lblSubtitle.Text = "Select Customer";
        }

        private void BtnHaddad_Click(object sender, EventArgs e)
        {
            this.Hide();
            using (var customerMenu = new CustomerMenu("HADDAD"))
            {
                customerMenu.ShowDialog();
            }
            this.Show();
        }

        private void BtnLtd_Click(object sender, EventArgs e)
        {
            this.Hide();
            using (var customerMenu = new CustomerMenu("LTD"))
            {
                customerMenu.ShowDialog();
            }
            this.Show();
        }

        private void BtnGaran_Click(object sender, EventArgs e)
        {
            this.Hide();
            using (var customerMenu = new CustomerMenu("GARAN"))
            {
                customerMenu.ShowDialog();
            }
            this.Show();
        }

        private void BtnExit_Click(object sender, EventArgs e)
        {
            Application.Exit();
        }
    }
}