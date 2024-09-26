---
name: Roadmap issue
about: Use this template for tracking release roadmaps.
title: "Roadmap for vXXXXX"
labels: roadmap
assignees: zimmski
---

Tasks/Goals:

- [ ] Development & Management 🛠️
  - [ ] TODO what and why as goal
- [ ] Documentation 📚
  - [ ] TODO what and why as goal
- [ ] Evaluation ⏱️
  - [ ] TODO what and why as goal
- [ ] Models 🤖
  - [ ] TODO what and why as goal
- [ ] Reports & Metrics 🗒️
  - [ ] TODO what and why as goal
- [ ] Operating Systems 🖥️
  - [ ] TODO what and why as goal
- [ ] Tools 🧰
  - [ ] TODO what and why as goal
- [ ] Tasks 🔢
  - [ ] TODO what and why as goal
- [ ] Closed PR / not-implemented issue 🚫
  - [ ] TODO what and why with reason

Release version of this roadmap issue:

> ❓ When should a release happen? Check the [`README`](../../README.md#when-and-how-to-release)!

- [ ] Do a full evaluation with the version
  - [ ] Exclude certain Openrouter models by default
    - [ ] `nitro` cause they are just faster
    - [ ] `extended` cause longer context windows don't matter for our tasks
    - [ ] `free` and `auto` cause these are just "aliases" for existing models
  - [ ] Exclude special-purpose models
    - [ ] Vision models
    - [ ] Roleplay and creative writing models
    - [ ] Classification models
    - [ ] Models with internet access (usually denoted by `-online` suffix)
    - [ ] Models with extended context windows (usually denoted by `-1234K` suffix)
  - [ ] Always prefer fine tuned (`-instruct`, `-chat`) models over a plain base model
- [ ] Tag version (tag can be moved in case important merges happen afterwards)
- [ ] For all issues of the current milestone, one by one, add them to the roadmap tasks (it is ok if a task has multiple issues) with the users that worked on it
  - Fixed bugs should always be sorted into respective relevant categories and not in a generic "Bugs" category!
- [ ] For all PRs of the current milestone, one by one, add them to the roadmap tasks (it is ok if a task has multiple issues) with the users that worked on it
  - Fixed bugs should always be sorted into respective relevant categories and not in a generic "Bugs" category!
- [ ] Search all issues for ...
  - [ ] Unassigned issues that are closed, and assign them someone
  - [ ] Issues without a milestone, and assign them a milestone
  - [ ] Issues without a label, and assign them at least one label
- [ ] Write the release notes:
  - [ ] Use the tasks that are already there for the release note outline
  - [ ] Add highlighted features based on the done tasks, sort by how many users would use the feature
- [ ] Do the release
  - [ ] With the release notes
  - [ ] Set as latest release
- [ ] Prepare the next roadmap
  - [ ] Create a milestone for the next release
  - [ ] Create a new roadmap issue for the next release
    - [ ] Move all open tasks/TODOs from this roadmap issue to the next roadmap issue.
    - [ ] Move every comment of this roadmap issue as a TODO to the next roadmap issue. Mark when done with a :rocket: emoji.
- [ ] Blog post containing evaluation results, new features and learnings
  - [ ] Update README with blog post link and new header image
  - [ ] Update repository link with blog post link
  - [ ] https://github.com/symflower/eval-dev-quality/discussions
    - [ ] Remove the previous announcements
    - [ ] Add a "Deep dive: $blog-post-title" announcement for the blog post
    - [ ] Add a "v$version: $summary-of-highlights" announcement for the release
- [ ] Announce release
- [ ] Eat cake 🎂

TODO sort and sort out:

- [ ] TODO
