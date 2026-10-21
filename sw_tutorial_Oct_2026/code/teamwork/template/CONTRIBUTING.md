# Rules of the game

These follow the way pull requests work in the ShipSoft repositories.

1. **One task, one branch, one pull request.** Name the branch
   `task-NN-short-description`, e.g. `task-07-fit`.
2. **Touch only your function.** Write between the `your code` markers of your
   task. Changes to the shared settings or to `run_pipeline` go in a pull
   request of their own, agreed with the organisers.
3. **Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):**
   `feat(task-07): fit the Breit-Wigner with a Poisson likelihood`.
   Use `fix(task-07): ...` for a correction after review.
4. **Test before you ask for review:** `pixi cvmfs check-task NN` must say
   `passed`, and `pixi cvmfs lint` must be clean. Paste the check output into
   the pull-request description.
5. **CI must be green.** Every push to a pull request runs the same checks
   (`pixi cvmfs check`, `pixi cvmfs lint`). If "All checks passed" is red, open
   the log of the failed job, reproduce it locally with the same pixi task,
   fix, and push again.
6. **Review:** your reviewer is the owner of the next task (task 10 is
   reviewed by the owner of task 1). Approve only what you have read and
   understood. Every review comment must be resolved before merging.
7. **Keep history linear.** `main` accepts no merge commits. If GitHub says
   your branch is out of date, rebase it:

   ```bash
   git fetch upstream
   git rebase upstream/main
   pixi cvmfs check-task NN
   git push --force-with-lease
   ```

8. **Never force-push to `main`,** and never rebase a branch somebody else
   has built on.
9. **Leave the environment alone.** Do not change `pixi.toml` or `pixi.lock`
   in a task pull request; propose environment changes separately.
