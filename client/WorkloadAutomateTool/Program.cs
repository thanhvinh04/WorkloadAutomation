using System;
using System.Windows.Forms;

namespace WorkloadAutomateTool
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new WorkloadAutomateTool.Forms.MainMenu());
        }
    }
}